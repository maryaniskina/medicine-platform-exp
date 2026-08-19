from django.core.exceptions import ValidationError as DjangoValidationError
from django.db import IntegrityError, transaction
from pydantic import ValidationError

from apps.clinics.models import Clinic
from apps.clinics.services.schemas import ClinicEvent, ClinicEventData
from apps.events.exceptions import PermanentEventError
from apps.events.models import ProcessedMessage


class ClinicEventError(PermanentEventError):
    pass


def parse_clinic_data(data: dict) -> dict:
    try:
        clinic_data = ClinicEventData.model_validate(data)
    except ValidationError as exc:
        raise ClinicEventError('Invalid clinic data') from exc

    return clinic_data.model_dump()


def parse_clinic_event(payload: dict) -> ClinicEvent:
    try:
        return ClinicEvent.model_validate(payload)
    except ValidationError as exc:
        raise ClinicEventError('Invalid clinic event payload') from exc


def validate_clinic(clinic: Clinic) -> None:
    try:
        clinic.full_clean()
    except DjangoValidationError as exc:
        if hasattr(exc, 'message_dict') and 'external_id' in exc.message_dict:
            raise PermanentEventError(str(exc)) from exc

        raise ClinicEventError(str(exc)) from exc


@transaction.atomic
def process_clinic_event(payload: dict) -> bool:
    event = parse_clinic_event(payload)

    try:
        with transaction.atomic():
            ProcessedMessage.objects.create(event_id=event.event_id)
    except IntegrityError:
        if ProcessedMessage.objects.filter(
            event_id=event.event_id,
        ).exists():
            return False
        raise

    clinic_data = event.data.model_dump(exclude_unset=True)
    external_id = clinic_data.pop('external_id')

    if clinic_data.get('email'):
        clinic_data['email'] = str(clinic_data['email']).lower()

    if event.event_type == 'clinic.created':
        clinic = Clinic(
            external_id=external_id,
            **clinic_data,
        )
        validate_clinic(clinic)

        try:
            clinic.save(force_insert=True)
        except IntegrityError as exc:
            raise PermanentEventError(
                'Clinic with this external_id already exists'
            ) from exc

    elif event.event_type == 'clinic.updated':
        try:
            clinic = Clinic.objects.select_for_update().get(
                external_id=external_id,
            )
        except Clinic.DoesNotExist as exc:
            raise PermanentEventError(
                'Cannot update a clinic that does not exist'
            ) from exc

        for field, value in clinic_data.items():
            setattr(clinic, field, value)

        validate_clinic(clinic)
        clinic.save()

    else:
        raise PermanentEventError('Unsupported event_type')

    return True
