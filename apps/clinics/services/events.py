from decimal import Decimal, InvalidOperation

from django.core.exceptions import ValidationError as DjangoValidationError
from django.db import IntegrityError, transaction

from apps.clinics.models import Clinic
from apps.events.exceptions import PermanentEventError
from apps.events.models import ProcessedMessage


class ClinicEventError(ValueError):
    pass


def parse_clinic_data(data: dict) -> dict:
    required_fields = {
        'external_id',
        'name',
        'address',
        'latitude',
        'longitude',
    }
    if not required_fields.issubset(data):
        raise ClinicEventError('Missing required clinic fields')

    for field in ('external_id', 'name', 'address'):
        value = data[field]
        if not isinstance(value, str) or not value.strip():
            raise ClinicEventError(f'{field} must be a non-empty string')

    try:
        latitude = Decimal(str(data['latitude']))
        longitude = Decimal(str(data['longitude']))
    except (InvalidOperation, ValueError):
        raise ClinicEventError('Invalid coordinates') from None

    if not latitude.is_finite() or not longitude.is_finite():
        raise ClinicEventError('Coordinates must be finite numbers')

    if not -90 <= latitude <= 90:
        raise ClinicEventError('Latitude must be between -90 and 90')

    if not -180 <= longitude <= 180:
        raise ClinicEventError('Longitude must be between -180 and 180')

    clinic_data = {
        'name': data['name'].strip(),
        'address': data['address'].strip(),
        'latitude': latitude,
        'longitude': longitude,
    }

    for field in ('phone', 'email'):
        value = data.get(field, '')
        if not isinstance(value, str):
            raise ClinicEventError(f'{field} must be a string')
        clinic_data[field] = value

    if 'is_active' in data:
        if not isinstance(data['is_active'], bool):
            raise ClinicEventError('is_active must be a boolean')
        clinic_data['is_active'] = data['is_active']

    return {
        'external_id': data['external_id'].strip(),
        **clinic_data,
    }


@transaction.atomic
def process_clinic_event(event: dict) -> bool:
    event_id = event['event_id']
    event_type = event['event_type']
    clinic_data = parse_clinic_data(event['data'])
    external_id = clinic_data.pop('external_id')

    try:
        with transaction.atomic():
            ProcessedMessage.objects.create(event_id=event_id)
    except IntegrityError:
        if ProcessedMessage.objects.filter(event_id=event_id).exists():
            return False
        raise

    if event_type == 'clinic.created':
        clinic = Clinic(external_id=external_id, **clinic_data)

        try:
            clinic.full_clean()
        except DjangoValidationError as exc:
            if 'external_id' in exc.message_dict:
                raise PermanentEventError(str(exc)) from exc
            raise ClinicEventError(str(exc)) from exc

        try:
            clinic.save(force_insert=True)
        except IntegrityError as exc:
            raise PermanentEventError(
                'Clinic with this external_id already exists'
            ) from exc

    elif event_type == 'clinic.updated':
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

        try:
            clinic.full_clean()
        except DjangoValidationError as exc:
            if 'external_id' in exc.message_dict:
                raise PermanentEventError(str(exc)) from exc
            raise ClinicEventError(str(exc)) from exc

        clinic.save()

    else:
        raise PermanentEventError('Unsupported event_type')

    return True
