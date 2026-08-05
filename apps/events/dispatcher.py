from apps.clinics.services.events import process_clinic_event
from apps.events.schemas.event import validate_event


def dispatch_event(payload: dict) -> bool:
    event = validate_event(payload)

    if event['event_type'] in {'clinic.created', 'clinic.updated'}:
        return process_clinic_event(event)

    return False