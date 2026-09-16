import pytest

from apps.appointments.models import Appointment
from apps.notifications.models import Notification
from apps.notifications.services import (
    create_appointment_reminders,
    mark_all_notifications_as_read,
    mark_notification_as_read,
    notify_appointment_booked,
    notify_appointment_cancelled,
)


@pytest.mark.django_db
class TestNotificationServices:
    def test_notifies_patient_and_doctor_about_booking(
        self,
        booking_appointment,
        booking_doctor_user,
    ):
        notify_appointment_booked(booking_appointment)

        assert Notification.objects.filter(
            recipient=booking_appointment.patient,
            notification_type=Notification.Type.APPOINTMENT_BOOKED,
        ).exists()
        assert Notification.objects.filter(
            recipient=booking_doctor_user,
            notification_type=Notification.Type.APPOINTMENT_BOOKED,
        ).exists()

    def test_booking_notification_is_idempotent(self, booking_appointment):
        notify_appointment_booked(booking_appointment)
        notify_appointment_booked(booking_appointment)

        assert Notification.objects.filter(
            appointment=booking_appointment,
            notification_type=Notification.Type.APPOINTMENT_BOOKED,
        ).count() == 1

    def test_notifies_after_cancellation(
        self,
        booking_appointment,
        booking_doctor_user,
    ):
        notify_appointment_cancelled(booking_appointment)

        assert Notification.objects.filter(
            recipient=booking_appointment.patient,
            notification_type=Notification.Type.APPOINTMENT_CANCELLED,
        ).exists()
        assert Notification.objects.filter(
            recipient=booking_doctor_user,
            notification_type=Notification.Type.APPOINTMENT_CANCELLED,
        ).exists()

    def test_creates_one_reminder_per_recipient(
        self,
        booking_appointment,
        booking_doctor_user,
    ):
        created_count = create_appointment_reminders([booking_appointment])
        repeated_count = create_appointment_reminders([booking_appointment])

        assert created_count == 2
        assert repeated_count == 0
        assert Notification.objects.filter(
            appointment=booking_appointment,
            notification_type=Notification.Type.APPOINTMENT_REMINDER,
        ).count() == 2

    def test_does_not_remind_cancelled_appointment(self, booking_appointment):
        booking_appointment.status = Appointment.Status.CANCELLED
        booking_appointment.save(update_fields=['status'])

        created_count = create_appointment_reminders([booking_appointment])

        assert created_count == 0

    def test_mark_notification_as_read(self, booking_appointment):
        notification = Notification.objects.create(
            recipient=booking_appointment.patient,
            appointment=booking_appointment,
            notification_type=Notification.Type.APPOINTMENT_BOOKED,
            title='Тест',
            message='Тестовое уведомление',
        )

        result = mark_notification_as_read(notification=notification)

        assert result.read_at is not None
        assert result.is_read is True

    def test_mark_all_notifications_as_read(self, booking_appointment):
        Notification.objects.create(
            recipient=booking_appointment.patient,
            appointment=booking_appointment,
            notification_type=Notification.Type.APPOINTMENT_BOOKED,
            title='Тест',
            message='Тестовое уведомление',
        )

        updated_count = mark_all_notifications_as_read(
            recipient=booking_appointment.patient,
        )

        assert updated_count == 1
        assert Notification.objects.filter(
            recipient=booking_appointment.patient,
            read_at__isnull=True,
        ).count() == 0
