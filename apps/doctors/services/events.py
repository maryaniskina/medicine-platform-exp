from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError as DjangoValidationError
from django.db import IntegrityError, transaction
from pydantic import ValidationError

from apps.clinics.models import Clinic
from apps.doctors.models import Doctor, DoctorClinic, Specialization
from apps.doctors.services.schemas import DoctorEvent
from apps.events.exceptions import PermanentEventError
from apps.events.models import ProcessedMessage


class DoctorEventError(PermanentEventError):
    pass


def parse_doctor_event(payload: dict) -> DoctorEvent:
    try:
        return DoctorEvent.model_validate(payload)
    except ValidationError as exc:
        raise DoctorEventError('Invalid doctor event payload') from exc


def get_doctor_user(email, first_name, last_name, external_id):
    User = get_user_model()
    user = (
        User.objects.select_for_update()
        .filter(
            email__iexact=email,
        )
        .first()
    )

    if user is None:
        return User.objects.create_user(
            email=email,
            password=None,
            first_name=first_name,
            last_name=last_name,
            role='doctor',
        )

    linked_doctor = (
        Doctor.objects.select_for_update()
        .filter(
            user=user,
        )
        .first()
    )
    if linked_doctor and linked_doctor.external_id != external_id:
        raise DoctorEventError('User is already linked to another doctor')

    if user.role != 'doctor':
        user.role = 'doctor'
        user.save(update_fields=['role'])

    return user


def update_specializations(doctor, names):
    specializations = []

    for name in names:
        specialization, _ = Specialization.objects.get_or_create(name=name)
        specializations.append(specialization)

    doctor.specializations.set(specializations)


def update_clinics(doctor, clinics_data):
    active_external_ids = set()

    for clinic_data in clinics_data:
        external_id = clinic_data.external_id
        active_external_ids.add(external_id)

        try:
            clinic = Clinic.objects.get(external_id=external_id)
        except Clinic.DoesNotExist as exc:
            raise DoctorEventError(f'Clinic {external_id} does not exist') from exc

        DoctorClinic.objects.update_or_create(
            doctor=doctor,
            clinic=clinic,
            defaults={
                'price': clinic_data.price,
                'duration_minutes': clinic_data.duration_minutes,
                'is_active': True,
            },
        )

    doctor.clinic_assignments.exclude(
        clinic__external_id__in=active_external_ids,
    ).update(is_active=False)


@transaction.atomic
def process_doctor_event(payload: dict) -> bool:
    raw_data = payload.get('data', {})
    event = parse_doctor_event(payload)

    _, message_created = ProcessedMessage.objects.get_or_create(
        event_id=event.event_id,
    )
    if not message_created:
        return False

    data = event.data
    supplied_fields = set(raw_data)
    email = str(data.email).strip().lower()
    external_id = data.external_id
    doctor_data = data.model_dump(
        exclude={
            'external_id',
            'email',
            'specializations',
            'clinics',
        },
        exclude_unset=True,
    )
    doctor_data.setdefault('photo_url', '')

    if doctor_data.get('photo_url'):
        doctor_data['photo_url'] = str(doctor_data['photo_url'])

    doctor = (
        Doctor.objects.select_for_update()
        .filter(
            external_id=external_id,
        )
        .first()
    )

    user = get_doctor_user(
        email=email,
        first_name=data.first_name,
        last_name=data.last_name,
        external_id=external_id,
    )

    if doctor and doctor.user_id and doctor.user_id != user.pk:
        raise DoctorEventError('Email does not match the user linked to this doctor')

    if doctor is None:
        doctor = Doctor(
            external_id=external_id,
            email=email,
            user=user,
            **doctor_data,
        )
        try:
            doctor.full_clean()
            doctor.save(force_insert=True)
        except DjangoValidationError as exc:
            raise DoctorEventError(str(exc)) from exc
        except IntegrityError as exc:
            raise PermanentEventError(
                'Doctor with this external_id or email already exists'
            ) from exc
    else:
        for field, value in doctor_data.items():
            setattr(doctor, field, value)

        doctor.email = email
        doctor.user = user
        try:
            with transaction.atomic():
                doctor.full_clean()
                doctor.save()
        except DjangoValidationError as exc:
            raise DoctorEventError(str(exc)) from exc
        except IntegrityError as exc:
            raise PermanentEventError(
                'Doctor with this external_id or email already exists'
            ) from exc

    if 'specializations' in supplied_fields:
        update_specializations(doctor, data.specializations)

    if 'clinics' in supplied_fields:
        update_clinics(doctor, data.clinics)

    return True
