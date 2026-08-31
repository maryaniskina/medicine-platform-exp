from datetime import timedelta

import pytest
from django.utils import timezone
from rest_framework.test import APIClient

from apps.appointments.models import Appointment

BASE_URL = '/api/appointments/'


@pytest.fixture
def api_client():
    return APIClient()


@pytest.mark.django_db
class TestCreateAppointmentAPI:
    def test_patient_can_create_appointment(
        self,
        api_client,
        booking_patient,
        booking_doctor_clinic,
        booking_schedule,
        booking_start,
    ):
        api_client.force_authenticate(booking_patient)

        response = api_client.post(
            BASE_URL,
            {
                'doctor_clinic_id': booking_doctor_clinic.pk,
                'start_at': booking_start.isoformat(),
                'patient_comment': 'Первичный приём',
            },
            format='json',
        )

        assert response.status_code == 201
        assert response.data['status'] == Appointment.Status.BOOKED
        assert response.data['clinic_name'] == booking_doctor_clinic.clinic.name
        assert response.data['patient_comment'] == 'Первичный приём'

    def test_anonymous_user_cannot_create_appointment(
        self,
        api_client,
        booking_doctor_clinic,
        booking_start,
    ):
        response = api_client.post(
            BASE_URL,
            {
                'doctor_clinic_id': booking_doctor_clinic.pk,
                'start_at': booking_start.isoformat(),
            },
            format='json',
        )

        assert response.status_code in (401, 403)

    def test_rejects_invalid_payload(self, api_client, booking_patient):
        api_client.force_authenticate(booking_patient)

        response = api_client.post(
            BASE_URL,
            {'doctor_clinic_id': 'invalid', 'start_at': 'not-a-datetime'},
            format='json',
        )

        assert response.status_code == 400


@pytest.mark.django_db
class TestPatientAppointmentListAPI:
    def test_returns_only_current_patients_appointments(
        self,
        api_client,
        booking_patient,
        another_booking_patient,
        booking_appointment,
        booking_doctor_clinic,
        booking_start,
    ):
        Appointment.objects.create(
            patient=another_booking_patient,
            doctor_clinic=booking_doctor_clinic,
            start_at=booking_start + timedelta(hours=1),
            end_at=booking_start + timedelta(hours=1, minutes=30),
        )
        api_client.force_authenticate(booking_patient)

        response = api_client.get(f'{BASE_URL}my/')

        assert response.status_code == 200
        assert response.data['count'] == 1
        assert response.data['results'][0]['id'] == booking_appointment.pk

    def test_filters_by_status(
        self,
        api_client,
        booking_patient,
        booking_appointment,
    ):
        api_client.force_authenticate(booking_patient)

        response = api_client.get(
            f'{BASE_URL}my/',
            {'status': Appointment.Status.BOOKED},
        )

        assert response.status_code == 200
        assert response.data['count'] == 1

    def test_rejects_unknown_status(
        self,
        api_client,
        booking_patient,
    ):
        api_client.force_authenticate(booking_patient)

        response = api_client.get(f'{BASE_URL}my/', {'status': 'unknown'})

        assert response.status_code == 400

    def test_rejects_date_and_range_together(
        self,
        api_client,
        booking_patient,
    ):
        api_client.force_authenticate(booking_patient)

        response = api_client.get(
            f'{BASE_URL}my/',
            {
                'date': timezone.localdate().isoformat(),
                'date_from': timezone.localdate().isoformat(),
                'date_to': timezone.localdate().isoformat(),
            },
        )

        assert response.status_code == 400


@pytest.mark.django_db
class TestCancelAppointmentAPI:
    def test_patient_can_cancel_own_appointment(
        self,
        api_client,
        booking_patient,
        booking_appointment,
    ):
        api_client.force_authenticate(booking_patient)

        response = api_client.post(
            f'{BASE_URL}{booking_appointment.pk}/cancel/',
            {'reason': 'Не смогу прийти'},
            format='json',
        )

        assert response.status_code == 200
        assert response.data['status'] == Appointment.Status.CANCELLED
        assert response.data['cancellation_reason'] == 'Не смогу прийти'

    def test_patient_cannot_cancel_another_patients_appointment(
        self,
        api_client,
        another_booking_patient,
        booking_appointment,
    ):
        api_client.force_authenticate(another_booking_patient)

        response = api_client.post(
            f'{BASE_URL}{booking_appointment.pk}/cancel/',
            {},
            format='json',
        )

        assert response.status_code == 400

    def test_cancel_rejects_too_long_reason(
        self,
        api_client,
        booking_patient,
        booking_appointment,
    ):
        api_client.force_authenticate(booking_patient)

        response = api_client.post(
            f'{BASE_URL}{booking_appointment.pk}/cancel/',
            {'reason': 'x' * 1001},
            format='json',
        )

        assert response.status_code == 400


@pytest.mark.django_db
class TestDoctorAppointmentListAPI:
    def test_doctor_sees_appointments_for_own_clinics(
        self,
        api_client,
        booking_doctor_user,
        booking_appointment,
    ):
        api_client.force_authenticate(booking_doctor_user)

        response = api_client.get(f'{BASE_URL}doctor/')

        assert response.status_code == 200
        assert response.data['count'] == 1
        assert response.data['results'][0]['id'] == booking_appointment.pk

    def test_patient_cannot_access_doctor_appointments(
        self,
        api_client,
        booking_patient,
    ):
        api_client.force_authenticate(booking_patient)

        response = api_client.get(f'{BASE_URL}doctor/')

        assert response.status_code == 403

    def test_doctor_can_filter_by_status(
        self,
        api_client,
        booking_doctor_user,
        booking_appointment,
    ):
        api_client.force_authenticate(booking_doctor_user)

        response = api_client.get(
            f'{BASE_URL}doctor/',
            {'status': Appointment.Status.BOOKED},
        )

        assert response.status_code == 200
        assert response.data['count'] == 1
