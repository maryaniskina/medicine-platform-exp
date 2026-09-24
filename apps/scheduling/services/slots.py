from datetime import date, datetime, time, timedelta

from django.db.models import Q
from django.utils import timezone

from apps.appointments.models import Appointment
from apps.doctors.models import DoctorClinic
from apps.scheduling.models import WeeklySchedule
from apps.scheduling.services.availability import is_slot_in_schedule


def generate_slots(
    doctor_clinic: DoctorClinic,
    selected_date: date,
) -> list[dict]:
    if isinstance(selected_date, datetime) or not isinstance(selected_date, date):
        raise TypeError('selected_date must be a date, not a datetime')

    if (
        not doctor_clinic.is_active
        or not doctor_clinic.doctor.is_active
        or not doctor_clinic.clinic.is_active
    ):
        return []

    local_timezone = timezone.get_default_timezone()
    day_start = timezone.make_aware(
        datetime.combine(selected_date, time.min),
        local_timezone,
    )
    day_end = timezone.make_aware(
        datetime.combine(selected_date + timedelta(days=1), time.min),
        local_timezone,
    )
    now = timezone.now()

    schedules = (
        WeeklySchedule.objects.filter(
            doctor_clinic=doctor_clinic,
            weekday=selected_date.weekday(),
            valid_from__lte=selected_date,
        )
        .filter(
            Q(valid_until__isnull=True) | Q(valid_until__gte=selected_date),
        )
        .order_by('start_time')
    )
    schedules = list(schedules)

    appointments = list(
        Appointment.objects.filter(
            doctor_clinic__doctor=doctor_clinic.doctor,
            status__in=[
                Appointment.Status.BOOKED,
                Appointment.Status.CONFIRMED,
            ],
            start_at__lt=day_end,
            end_at__gt=day_start,
        ).values_list('start_at', 'end_at')
    )

    duration = timedelta(minutes=doctor_clinic.duration_minutes)
    slots = {}

    for schedule in schedules:
        current_start = datetime.combine(
            selected_date,
            schedule.start_time,
        )
        schedule_end = datetime.combine(
            selected_date,
            schedule.end_time,
        )

        while current_start + duration <= schedule_end:
            current_end = current_start + duration
            aware_start = timezone.make_aware(
                current_start,
                local_timezone,
            )
            aware_end = timezone.make_aware(
                current_end,
                local_timezone,
            )

            if not is_slot_in_schedule(
                schedules=schedules,
                start_at=aware_start,
                end_at=aware_end,
                duration_minutes=doctor_clinic.duration_minutes,
            ):
                current_start = current_end
                continue

            is_booked = any(
                appointment_start < aware_end and appointment_end > aware_start
                for appointment_start, appointment_end in appointments
            )

            if aware_start > now and not is_booked:
                slots[aware_start] = {
                    'start': aware_start,
                    'end': aware_end,
                }

            current_start = current_end

    return sorted(
        slots.values(),
        key=lambda slot: slot['start'],
    )
