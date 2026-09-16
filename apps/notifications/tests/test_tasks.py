from datetime import timedelta

import pytest
from django.utils import timezone

from apps.notifications.models import Notification


@pytest.mark.django_db
class TestAppointmentReminderTask:
    def test_task_finds_appointments_24_hours_ahead(
        self,
        booking_appointment,
        monkeypatch,
    ):
        from apps.notifications import tasks

        now = timezone.now()
        booking_appointment.start_at = now + timedelta(hours=24, minutes=1)
        booking_appointment.end_at = booking_appointment.start_at + timedelta(
            minutes=30,
        )
        booking_appointment.save(update_fields=['start_at', 'end_at'])
        monkeypatch.setattr(tasks.timezone, 'now', lambda: now)

        created_count = tasks.send_appointment_reminders.run()

        assert created_count == 1
        assert Notification.objects.filter(
            appointment=booking_appointment,
            notification_type=Notification.Type.APPOINTMENT_REMINDER,
        ).count() == 1
