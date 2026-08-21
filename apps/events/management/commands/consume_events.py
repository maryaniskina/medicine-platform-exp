import json
import logging
import os

import pika
from django.core.management.base import BaseCommand

from apps.clinics.services.events import ClinicEventError
from apps.doctors.services.events import DoctorEventError
from apps.events.dispatcher import dispatch_event
from apps.events.exceptions import PermanentEventError
from apps.events.schemas.event import EventValidationError
from common.rabbitmq.topology import (
    DLQ_NAME,
    DLX_NAME,
    EXCHANGE_NAME,
    MAX_RETRIES,
    QUEUE_NAME,
    RETRY_DELAY_MS,
    RETRY_EXCHANGE_NAME,
    RETRY_QUEUE_NAME,
)

logger = logging.getLogger(__name__)


PERMANENT_ERRORS = (
    json.JSONDecodeError,
    EventValidationError,
    ClinicEventError,
    PermanentEventError,
    DoctorEventError,
)


def declare_topology(channel):
    channel.exchange_declare(
        exchange=EXCHANGE_NAME,
        exchange_type='topic',
        durable=True,
    )
    channel.exchange_declare(
        exchange=RETRY_EXCHANGE_NAME,
        exchange_type='direct',
        durable=True,
    )
    channel.exchange_declare(
        exchange=DLX_NAME,
        exchange_type='topic',
        durable=True,
    )

    channel.queue_declare(
        queue=DLQ_NAME,
        durable=True,
    )
    channel.queue_bind(
        exchange=DLX_NAME,
        queue=DLQ_NAME,
        routing_key='dead',
    )

    channel.queue_declare(
        queue=RETRY_QUEUE_NAME,
        durable=True,
        arguments={
            'x-message-ttl': RETRY_DELAY_MS,
            'x-dead-letter-exchange': EXCHANGE_NAME,
            'x-dead-letter-routing-key': 'retry',
        },
    )
    channel.queue_bind(
        exchange=RETRY_EXCHANGE_NAME,
        queue=RETRY_QUEUE_NAME,
        routing_key='retry',
    )

    channel.queue_declare(
        queue=QUEUE_NAME,
        durable=True,
        arguments={
            'x-dead-letter-exchange': DLX_NAME,
            'x-dead-letter-routing-key': 'dead',
        },
    )
    channel.queue_bind(
        exchange=EXCHANGE_NAME,
        queue=QUEUE_NAME,
        routing_key='#',
    )


def get_retry_count(properties) -> int:
    headers = properties.headers or {}
    try:
        return max(0, int(headers.get('x-medbook-retries', 0)))
    except (TypeError, ValueError):
        return 0


def publish_message(
    channel,
    exchange: 'str',
    routing_key: 'str',
    body: bytes,
    properties,
    retries: int,
) -> None:
    headers = dict(properties.headers or {})
    headers['x-medbook-retries'] = retries

    new_properties = pika.BasicProperties(
        content_type=properties.content_type or 'application/json',
        content_encoding=properties.content_encoding,
        delivery_mode=2,
        headers=headers,
        priority=properties.priority,
        correlation_id=properties.correlation_id,
        reply_to=properties.reply_to,
        expiration=None,
        message_id=properties.message_id,
        timestamp=properties.timestamp,
        type=properties.type,
        app_id=properties.app_id,
    )

    channel.basic_publish(
        exchange=exchange,
        routing_key=routing_key,
        body=body,
        properties=new_properties,
        mandatory=True,
    )


def reject_permanently(
    channel,
    method,
    body: bytes,
    properties,
) -> None:
    publish_message(
        channel=channel,
        exchange=DLX_NAME,
        routing_key='dead',
        body=body,
        properties=properties,
        retries=get_retry_count(properties),
    )
    channel.basic_ack(delivery_tag=method.delivery_tag)


def retry_or_reject(
    channel,
    method,
    body: bytes,
    properties,
) -> None:
    retries = get_retry_count(properties) + 1

    if retries <= MAX_RETRIES:
        publish_message(
            channel=channel,
            exchange=RETRY_EXCHANGE_NAME,
            routing_key='retry',
            body=body,
            properties=properties,
            retries=retries,
        )
        logger.warning(
            'Event scheduled for retry %s/%s',
            retries,
            MAX_RETRIES,
        )
    else:
        publish_message(
            channel=channel,
            exchange=DLX_NAME,
            routing_key='dead',
            body=body,
            properties=properties,
            retries=retries,
        )
        logger.error('Event exceeded retry limit; sent to DLQ')

    channel.basic_ack(delivery_tag=method.delivery_tag)


def handle_message(channel, method, properties, body: bytes) -> None:
    logger.info(
        'Received RabbitMQ message: routing_key=%s, body=%s',
        method.routing_key,
        body.decode('utf-8', errors='replace'),
    )
    try:
        payload = json.loads(body)
        dispatch_event(payload)
    except PERMANENT_ERRORS as exc:
        logger.warning('Rejecting invalid event: %s', exc)
        try:
            reject_permanently(channel, method, body, properties)
        except Exception:
            logger.exception('Failed to publish event to DLQ')
            channel.basic_nack(
                delivery_tag=method.delivery_tag,
                requeue=True,
            )
    except Exception:
        logger.exception('Temporary or unexpected event processing failure')
        try:
            retry_or_reject(channel, method, body, properties)
        except Exception:
            logger.exception('Failed to publish event for retry or DLQ')
            channel.basic_nack(
                delivery_tag=method.delivery_tag,
                requeue=True,
            )
    else:
        channel.basic_ack(delivery_tag=method.delivery_tag)
        logger.info('Event processed successfully')


class Command(BaseCommand):
    help = 'Consume MedBook events from RabbitMQ'

    def handle(self, *args, **options):
        rabbitmq_url = os.environ['RABBITMQ_URL']
        parameters = pika.URLParameters(rabbitmq_url)
        connection = pika.BlockingConnection(parameters)
        channel = connection.channel()

        try:
            declare_topology(channel)
            channel.confirm_delivery()
            channel.basic_qos(prefetch_count=1)
            channel.basic_consume(
                queue=QUEUE_NAME,
                on_message_callback=handle_message,
                auto_ack=False,
            )

            self.stdout.write(self.style.SUCCESS('Waiting for RabbitMQ events...'))
            channel.start_consuming()
        except KeyboardInterrupt:
            self.stdout.write('Stopping RabbitMQ consumer...')
            if channel.is_open:
                channel.stop_consuming()
        finally:
            if connection.is_open:
                connection.close()
