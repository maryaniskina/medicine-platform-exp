from datetime import timedelta

import pytest
from django.core.exceptions import ValidationError
from django.utils import timezone

from apps.appointments.models import Appointment


@pytest.mark.django_db
class TestAppointmentModel:
    def test_defaults_to_booked_status(self, booking_appointment):
        assert booking_appointment.status == Appointment.Status.BOOKED

    def test_rejects_end_before_start(
        self,
        booking_patient,
        booking_doctor_clinic,
        booking_start,
    ):
        appointment = Appointment(
            patient=booking_patient,
            doctor_clinic=booking_doctor_clinic,
            start_at=booking_start,
            end_at=booking_start - timedelta(minutes=30),
        )

        with pytest.raises(ValidationError):
            appointment.full_clean()

    def test_rejects_past_start_time_when_creating(
        self,
        booking_patient,
        booking_doctor_clinic,
    ):
        now = timezone.now()
        appointment = Appointment(
            patient=booking_patient,
            doctor_clinic=booking_doctor_clinic,
            start_at=now - timedelta(minutes=30),
            end_at=now,
        )

        with pytest.raises(ValidationError, match='прошедшее время'):
            appointment.full_clean()

    def test_sets_cancelled_at_when_saved_as_cancelled(
        self,
        booking_patient,
        booking_doctor_clinic,
        booking_start,
    ):
        appointment = Appointment.objects.create(
            patient=booking_patient,
            doctor_clinic=booking_doctor_clinic,
            start_at=booking_start,
            end_at=booking_start + timedelta(minutes=30),
            status=Appointment.Status.CANCELLED,
        )

        assert appointment.cancelled_at is not None
