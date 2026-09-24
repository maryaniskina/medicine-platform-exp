import pytest

from apps.notifications.models import Notification
from apps.notifications.serializers import NotificationSerializer


@pytest.mark.django_db
class TestNotificationSerializer:
    def test_serializes_public_fields(self, booking_appointment):
        notification = Notification.objects.create(
            recipient=booking_appointment.patient,
            appointment=booking_appointment,
            notification_type=Notification.Type.APPOINTMENT_BOOKED,
            title='Запись создана',
            message='Вы записаны на приём',
        )

        data = NotificationSerializer(notification).data

        assert data['id'] == notification.pk
        assert data['notification_type'] == (Notification.Type.APPOINTMENT_BOOKED)
        assert data['title'] == 'Запись создана'
        assert data['message'] == 'Вы записаны на приём'
        assert data['is_read'] is False
        assert data['read_at'] is None
