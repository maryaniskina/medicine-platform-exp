import pytest
from rest_framework.test import APIClient

from apps.notifications.models import Notification


@pytest.mark.django_db
class TestNotificationAPI:
    def setup_method(self):
        self.client = APIClient()

    def test_requires_authentication(self):
        response = self.client.get('/api/notifications/')

        assert response.status_code == 403

    def test_lists_only_current_users_notifications(
        self,
        booking_appointment,
        another_booking_patient,
    ):
        own_notification = Notification.objects.create(
            recipient=booking_appointment.patient,
            appointment=booking_appointment,
            notification_type=Notification.Type.APPOINTMENT_BOOKED,
            title='Моё уведомление',
            message='Текст',
        )
        Notification.objects.create(
            recipient=another_booking_patient,
            appointment=booking_appointment,
            notification_type=Notification.Type.APPOINTMENT_BOOKED,
            title='Чужое уведомление',
            message='Текст',
        )
        self.client.force_authenticate(booking_appointment.patient)

        response = self.client.get('/api/notifications/')

        assert response.status_code == 200
        assert response.data['count'] == 1
        assert response.data['results'][0]['id'] == own_notification.pk

    def test_counts_unread_notifications(self, booking_appointment):
        Notification.objects.create(
            recipient=booking_appointment.patient,
            appointment=booking_appointment,
            notification_type=Notification.Type.APPOINTMENT_BOOKED,
            title='Тест',
            message='Текст',
        )
        self.client.force_authenticate(booking_appointment.patient)

        response = self.client.get('/api/notifications/unread-count/')

        assert response.status_code == 200
        assert response.data['unread_count'] == 1

    def test_user_cannot_mark_another_users_notification_as_read(
        self,
        booking_appointment,
        another_booking_patient,
    ):
        notification = Notification.objects.create(
            recipient=another_booking_patient,
            appointment=booking_appointment,
            notification_type=Notification.Type.APPOINTMENT_BOOKED,
            title='Чужое уведомление',
            message='Текст',
        )
        self.client.force_authenticate(booking_appointment.patient)

        response = self.client.patch(
            f'/api/notifications/{notification.pk}/read/',
        )

        assert response.status_code == 404
        notification.refresh_from_db()
        assert notification.read_at is None

    def test_marks_all_notifications_as_read(self, booking_appointment):
        Notification.objects.create(
            recipient=booking_appointment.patient,
            appointment=booking_appointment,
            notification_type=Notification.Type.APPOINTMENT_BOOKED,
            title='Тест',
            message='Текст',
        )
        self.client.force_authenticate(booking_appointment.patient)

        response = self.client.post('/api/notifications/read-all/')

        assert response.status_code == 200
        assert response.data['updated_count'] == 1
