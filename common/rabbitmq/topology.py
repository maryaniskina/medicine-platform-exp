EXCHANGE_NAME = 'medbook.events'
RETRY_EXCHANGE_NAME = 'medbook.events.retry'
DLX_NAME = 'medbook.events.dlx'

QUEUE_NAME = 'medbook.events.incoming'
RETRY_QUEUE_NAME = 'medbook.events.retry'
DLQ_NAME = 'medbook.events.dlq'

MAX_RETRIES = 3
RETRY_DELAY_MS = 30000
