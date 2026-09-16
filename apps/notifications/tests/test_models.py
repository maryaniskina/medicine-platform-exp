import pytest

from apps.notifications.models import Notification


@pytest.mark.django_db
class TestNotificationModel:
    def test_notification_is_unread_by_default(self, booking_appointment):
        notification = Notification.objects.create(
            recipient=booking_appointment.patient,
            appointment=booking_appointment,
            notification_type=Notification.Type.APPOINTMENT_BOOKED,
            title='Тест',
            message='Текст',
        )

        assert notification.read_at is None
        assert notification.is_read is False

    def test_notification_can_be_marked_as_read(
        self,
        booking_appointment,
    ):
        notification = Notification.objects.create(
            recipient=booking_appointment.patient,
            appointment=booking_appointment,
            notification_type=Notification.Type.APPOINTMENT_BOOKED,
            title='Тест',
            message='Текст',
        )
        notification.read_at = notification.created_at
        notification.save(update_fields=['read_at'])

        notification.refresh_from_db()

        assert notification.is_read is True
