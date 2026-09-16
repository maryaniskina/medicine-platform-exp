from datetime import datetime, timedelta

from django.db import transaction
from django.db.models import Q
from django.utils import timezone
from rest_framework.exceptions import ValidationError

from apps.appointments.models import Appointment
from apps.doctors.models import Doctor, DoctorClinic
from apps.scheduling.models import WeeklySchedule
from apps.scheduling.services.availability import is_slot_in_schedule


@transaction.atomic
def create_appointment(
    *,
    patient,
    doctor_clinic_id,
    start_at,
    patient_comment='',
):
    if not patient.is_authenticated:
        raise ValidationError('Необходимо авторизоваться.')

    if patient.role != patient.Role.PATIENT:
        raise ValidationError('Записаться на приём может только пациент.')

    if not isinstance(start_at, datetime) or not timezone.is_aware(start_at):
        raise ValidationError({
            'start_at': 'Укажи дату и время с часовым поясом.',
        })

    if start_at <= timezone.now():
        raise ValidationError({
            'start_at': 'Нельзя записаться на прошедшее время.',
        })

    doctor_id = DoctorClinic.objects.filter(
        pk=doctor_clinic_id,
    ).values_list('doctor_id', flat=True).first()

    if doctor_id is None:
        raise ValidationError({
            'doctor_clinic_id': 'Врач в указанной клинике не найден.',
        })

    doctor = Doctor.objects.select_for_update().get(pk=doctor_id)

    try:
        doctor_clinic = DoctorClinic.objects.select_related(
            'clinic',
        ).get(
            pk=doctor_clinic_id,
            doctor=doctor,
        )
    except DoctorClinic.DoesNotExist:
        raise ValidationError({
            'doctor_clinic_id': 'Врач в указанной клинике не найден.',
        })

    if (
        not doctor.is_active
        or not doctor_clinic.is_active
        or not doctor_clinic.clinic.is_active
    ):
        raise ValidationError('Врач сейчас недоступен для записи.')

    local_timezone = timezone.get_default_timezone()
    local_start = timezone.localtime(start_at, local_timezone)
    duration = timedelta(minutes=doctor_clinic.duration_minutes)
    end_at = start_at + duration
    local_end = timezone.localtime(end_at, local_timezone)

    if local_end.date() != local_start.date():
        raise ValidationError({
            'start_at': 'Приём не может выходить за пределы рабочего дня.',
        })

    schedules = list(
        WeeklySchedule.objects.filter(
            doctor_clinic=doctor_clinic,
            weekday=local_start.weekday(),
            valid_from__lte=local_start.date(),
        ).filter(
            Q(valid_until__isnull=True)
            | Q(valid_until__gte=local_start.date()),
        )
    )

    if not is_slot_in_schedule(
        schedules=schedules,
        start_at=start_at,
        end_at=end_at,
        duration_minutes=doctor_clinic.duration_minutes,
    ):
        raise ValidationError({
            'start_at': (
                'Время не соответствует расписанию '
                'или сетке доступных слотов.'
            ),
        })

    active_statuses = [
        Appointment.Status.BOOKED,
        Appointment.Status.CONFIRMED,
    ]

    has_conflict = Appointment.objects.filter(
        doctor_clinic__doctor=doctor,
        status__in=active_statuses,
        start_at__lt=end_at,
        end_at__gt=start_at,
    ).exists()

    if has_conflict:
        raise ValidationError({
            'start_at': 'Это время уже занято. Выбери другой слот.',
        })

    appointment = Appointment.objects.create(
        patient=patient,
        doctor_clinic=doctor_clinic,
        start_at=start_at,
        end_at=end_at,
        patient_comment=patient_comment,
    )

    from apps.notifications.services import notify_appointment_booked
    notify_appointment_booked(appointment)

    return appointment


@transaction.atomic
def cancel_appointment(*, patient, appointment_id, reason=''):
    try:
        appointment = Appointment.objects.select_for_update().get(
            pk=appointment_id,
            patient=patient,
        )
    except Appointment.DoesNotExist:
        raise ValidationError({
            'appointment_id': 'Запись не найдена.',
        })

    if appointment.status not in {
        Appointment.Status.BOOKED,
        Appointment.Status.CONFIRMED,
    }:
        raise ValidationError({
            'status': 'Эту запись нельзя отменить.',
        })

    if appointment.start_at <= timezone.now():
        raise ValidationError({
            'start_at': 'Нельзя отменить уже начавшийся приём.',
        })

    appointment.status = Appointment.Status.CANCELLED
    appointment.cancellation_reason = reason
    appointment.cancelled_at = timezone.now()
    appointment.save(
        update_fields=[
            'status',
            'cancellation_reason',
            'cancelled_at',
            'updated_at',
        ],
    )

    from apps.notifications.services import notify_appointment_cancelled
    notify_appointment_cancelled(appointment)

    return appointment
