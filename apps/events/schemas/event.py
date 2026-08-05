from typing import Any


class EventValidationError(ValueError):
    pass


def validate_event(payload: Any) -> dict:
    if not isinstance(payload, dict):
        raise EventValidationError('Event must be a JSON object')

    required_fields = {'event_id', 'event_type', 'version', 'data'}
    if not required_fields.issubset(payload):
        raise EventValidationError('Missing required event fields')

    if not isinstance(payload['event_id'], str) or not payload['event_id'].strip():
        raise EventValidationError('event_id must be a non-empty string')

    if payload['event_type'] not in {'clinic.created', 'clinic.updated'}:
        raise EventValidationError('Unsupported event_type')

    if payload['version'] != 1:
        raise EventValidationError('Unsupported event version')

    if not isinstance(payload['data'], dict):
        raise EventValidationError('data must be a JSON object')

    return payload
