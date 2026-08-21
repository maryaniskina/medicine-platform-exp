from apps.clinics.services.events import process_clinic_event
from apps.doctors.services.events import process_doctor_event
from apps.events.schemas.event import validate_event


def dispatch_event(payload: dict) -> bool:
    event = validate_event(payload)
    event_type = event['event_type']

    if event_type in {'clinic.created', 'clinic.updated'}:
        return process_clinic_event(event)

    if event_type in {'doctor.created', 'doctor.updated'}:
        return process_doctor_event(event)

    return False
