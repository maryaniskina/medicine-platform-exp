from datetime import timedelta

from celery import shared_task
from django.utils import timezone

from apps.appointments.models import Appointment
from apps.notifications.services import create_appointment_reminders


@shared_task
def send_appointment_reminders():
    now = timezone.now()
    reminder_start = now + timedelta(hours=24)
    reminder_end = reminder_start + timedelta(minutes=2)
    appointments = Appointment.objects.filter(
        status__in=[
            Appointment.Status.BOOKED,
            Appointment.Status.CONFIRMED,
        ],
        start_at__gte=reminder_start,
        start_at__lt=reminder_end,
    ).select_related(
        'patient',
        'doctor_clinic__doctor__user',
        'doctor_clinic__clinic',
    )
    return create_appointment_reminders(appointments)
