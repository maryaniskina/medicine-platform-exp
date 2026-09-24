from datetime import datetime, time, timedelta

import pytest
from rest_framework.test import APIClient

from apps.appointments.models import Appointment
from apps.doctors.models import DoctorClinic
from apps.scheduling.services.slots import generate_slots

BASE_URL = '/api/scheduling/slots/'


@pytest.fixture
def api_client():
    return APIClient()


@pytest.mark.django_db
class TestGenerateSlots:
    def test_generates_slots_inside_schedule(
        self,
        booking_doctor_clinic,
        booking_schedule,
        booking_date,
    ):
        slots = generate_slots(booking_doctor_clinic, booking_date)

        assert len(slots) == 6
        assert slots[0]['start'].time() == time(9, 0)
        assert slots[-1]['start'].time() == time(11, 30)
        assert all(
            slot['end'] - slot['start'] == timedelta(minutes=30) for slot in slots
        )

    def test_excludes_booked_slot(
        self,
        booking_doctor_clinic,
        booking_schedule,
        booking_date,
        booking_appointment,
    ):
        slots = generate_slots(booking_doctor_clinic, booking_date)
        starts = [slot['start'] for slot in slots]

        assert booking_appointment.start_at not in starts
        assert len(slots) == 5

    def test_excludes_slots_booked_in_another_clinic(
        self,
        booking_doctor,
        booking_doctor_clinic,
        booking_schedule,
        booking_date,
        booking_patient,
        booking_start,
    ):
        from decimal import Decimal

        from apps.clinics.models import Clinic

        other_clinic = Clinic.objects.create(
            external_id='test-clinic-002',
            name='Вторая клиника',
            address='Москва, Вторая улица, 2',
            latitude=Decimal('55.760000'),
            longitude=Decimal('37.620000'),
        )
        other_assignment = DoctorClinic.objects.create(
            doctor=booking_doctor,
            clinic=other_clinic,
            duration_minutes=30,
        )
        Appointment.objects.create(
            patient=booking_patient,
            doctor_clinic=other_assignment,
            start_at=booking_start,
            end_at=booking_start + timedelta(minutes=30),
        )

        slots = generate_slots(booking_doctor_clinic, booking_date)

        assert booking_start not in [slot['start'] for slot in slots]

    def test_returns_no_slots_for_inactive_doctor(
        self,
        booking_doctor_clinic,
        booking_date,
    ):
        booking_doctor_clinic.doctor.is_active = False
        booking_doctor_clinic.doctor.save(update_fields=['is_active'])

        assert generate_slots(booking_doctor_clinic, booking_date) == []

    def test_rejects_datetime_instead_of_date(
        self,
        booking_doctor_clinic,
        booking_date,
    ):
        with pytest.raises(TypeError):
            generate_slots(
                booking_doctor_clinic,
                datetime.combine(booking_date, time(10, 0)),
            )


@pytest.mark.django_db
class TestAvailableSlotsAPI:
    def test_returns_slots_without_authentication(
        self,
        api_client,
        booking_doctor_clinic,
        booking_schedule,
        booking_date,
    ):
        response = api_client.get(
            BASE_URL,
            {
                'doctor_clinic_id': booking_doctor_clinic.pk,
                'date': booking_date.isoformat(),
            },
        )

        assert response.status_code == 200
        assert response.data['doctor_clinic_id'] == booking_doctor_clinic.pk
        assert response.data['date'] == booking_date
        assert len(response.data['slots']) == 6

    @pytest.mark.parametrize(
        'params',
        [
            {'date': '2026-10-26'},
            {'doctor_clinic_id': '1'},
            {'doctor_clinic_id': 'abc', 'date': '2026-10-26'},
            {'doctor_clinic_id': '1', 'date': 'not-a-date'},
        ],
    )
    def test_rejects_invalid_query_parameters(self, api_client, params):
        response = api_client.get(BASE_URL, params)

        assert response.status_code == 400

    def test_returns_404_for_inactive_assignment(
        self,
        api_client,
        booking_doctor_clinic,
        booking_date,
    ):
        booking_doctor_clinic.is_active = False
        booking_doctor_clinic.save(update_fields=['is_active'])

        response = api_client.get(
            BASE_URL,
            {
                'doctor_clinic_id': booking_doctor_clinic.pk,
                'date': booking_date.isoformat(),
            },
        )

        assert response.status_code == 404
