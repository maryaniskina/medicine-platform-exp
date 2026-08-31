from datetime import timedelta

import pytest
from django.contrib.auth import get_user_model
from django.utils import timezone
from rest_framework.exceptions import ValidationError

from apps.appointments.models import Appointment
from apps.appointments.services import cancel_appointment, create_appointment
from apps.clinics.models import Clinic
from apps.doctors.models import DoctorClinic


@pytest.mark.django_db
class TestCreateAppointment:
    def test_creates_appointment_for_valid_slot(
        self,
        booking_patient,
        booking_doctor_clinic,
        booking_schedule,
        booking_start,
    ):
        appointment = create_appointment(
            patient=booking_patient,
            doctor_clinic_id=booking_doctor_clinic.pk,
            start_at=booking_start,
            patient_comment='Болит горло',
        )

        assert appointment.pk is not None
        assert appointment.patient == booking_patient
        assert appointment.doctor_clinic == booking_doctor_clinic
        assert appointment.start_at == booking_start
        assert appointment.end_at == booking_start + timedelta(minutes=30)
        assert appointment.patient_comment == 'Болит горло'
        assert appointment.status == Appointment.Status.BOOKED

    def test_rejects_anonymous_patient(
        self,
        booking_doctor_clinic,
        booking_start,
    ):
        from django.contrib.auth.models import AnonymousUser

        with pytest.raises(ValidationError, match='авторизоваться'):
            create_appointment(
                patient=AnonymousUser(),
                doctor_clinic_id=booking_doctor_clinic.pk,
                start_at=booking_start,
            )

    def test_rejects_user_with_doctor_role(
        self,
        booking_doctor_clinic,
        booking_start,
    ):
        user_model = get_user_model()
        doctor_user = user_model.objects.create_user(
            email='not-a-patient@example.com',
            password='StrongPassword123!',
            first_name='Доктор',
            last_name='Иванов',
            role=user_model.Role.DOCTOR,
        )

        with pytest.raises(ValidationError, match='только пациент'):
            create_appointment(
                patient=doctor_user,
                doctor_clinic_id=booking_doctor_clinic.pk,
                start_at=booking_start,
            )

    def test_rejects_past_start_time(
        self,
        booking_patient,
        booking_doctor_clinic,
    ):
        with pytest.raises(ValidationError, match='прошедшее время'):
            create_appointment(
                patient=booking_patient,
                doctor_clinic_id=booking_doctor_clinic.pk,
                start_at=timezone.now() - timedelta(days=1),
            )

    def test_rejects_unknown_doctor_clinic(
        self,
        booking_patient,
        booking_start,
    ):
        with pytest.raises(ValidationError, match='не найден'):
            create_appointment(
                patient=booking_patient,
                doctor_clinic_id=999999,
                start_at=booking_start,
            )

    @pytest.mark.parametrize('inactive_target', ['doctor', 'clinic', 'assignment'])
    def test_rejects_inactive_booking_target(
        self,
        booking_patient,
        booking_doctor_clinic,
        booking_start,
        booking_schedule,
        inactive_target,
    ):
        if inactive_target == 'doctor':
            booking_doctor_clinic.doctor.is_active = False
            booking_doctor_clinic.doctor.save(update_fields=['is_active'])
        elif inactive_target == 'clinic':
            booking_doctor_clinic.clinic.is_active = False
            booking_doctor_clinic.clinic.save(update_fields=['is_active'])
        else:
            booking_doctor_clinic.is_active = False
            booking_doctor_clinic.save(update_fields=['is_active'])

        with pytest.raises(ValidationError, match='недоступен'):
            create_appointment(
                patient=booking_patient,
                doctor_clinic_id=booking_doctor_clinic.pk,
                start_at=booking_start,
            )

    def test_rejects_slot_outside_schedule(
        self,
        booking_patient,
        booking_doctor_clinic,
        booking_schedule,
        booking_start,
    ):
        with pytest.raises(ValidationError, match='не соответствует расписанию'):
            create_appointment(
                patient=booking_patient,
                doctor_clinic_id=booking_doctor_clinic.pk,
                start_at=booking_start + timedelta(minutes=15),
            )

    def test_rejects_conflicting_appointment(
        self,
        booking_patient,
        booking_doctor_clinic,
        booking_schedule,
        booking_start,
        booking_appointment,
    ):
        with pytest.raises(ValidationError, match='уже занято'):
            create_appointment(
                patient=booking_patient,
                doctor_clinic_id=booking_doctor_clinic.pk,
                start_at=booking_start,
            )

    def test_rejects_conflict_in_another_clinic(
        self,
        booking_patient,
        booking_doctor,
        booking_doctor_clinic,
        booking_schedule,
        booking_start,
    ):
        from decimal import Decimal

        other_clinic = Clinic.objects.create(
            external_id='test-clinic-003',
            name='Другая клиника',
            address='Москва, Другая улица, 3',
            latitude=Decimal('55.770000'),
            longitude=Decimal('37.630000'),
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

        with pytest.raises(ValidationError, match='уже занято'):
            create_appointment(
                patient=booking_patient,
                doctor_clinic_id=booking_doctor_clinic.pk,
                start_at=booking_start,
            )

    def test_rejects_appointment_crossing_local_day_boundary(
        self,
        booking_patient,
        booking_doctor_clinic,
        booking_date,
    ):
        from datetime import datetime, time

        local_timezone = timezone.get_default_timezone()
        start_at = timezone.make_aware(
            datetime.combine(booking_date, time(23, 45)),
            local_timezone,
        )

        with pytest.raises(ValidationError, match='пределы рабочего дня'):
            create_appointment(
                patient=booking_patient,
                doctor_clinic_id=booking_doctor_clinic.pk,
                start_at=start_at,
            )


@pytest.mark.django_db
class TestCancelAppointment:
    def test_cancels_own_future_appointment(
        self,
        booking_patient,
        booking_appointment,
    ):
        appointment = cancel_appointment(
            patient=booking_patient,
            appointment_id=booking_appointment.pk,
            reason='Изменились планы',
        )

        appointment.refresh_from_db()
        assert appointment.status == Appointment.Status.CANCELLED
        assert appointment.cancellation_reason == 'Изменились планы'
        assert appointment.cancelled_at is not None

    def test_patient_cannot_cancel_another_patients_appointment(
        self,
        another_booking_patient,
        booking_appointment,
    ):
        with pytest.raises(ValidationError, match='не найдена'):
            cancel_appointment(
                patient=another_booking_patient,
                appointment_id=booking_appointment.pk,
            )

    def test_cannot_cancel_already_cancelled_appointment(
        self,
        booking_patient,
        booking_appointment,
    ):
        booking_appointment.status = Appointment.Status.CANCELLED
        booking_appointment.save(update_fields=['status'])

        with pytest.raises(ValidationError, match='нельзя отменить'):
            cancel_appointment(
                patient=booking_patient,
                appointment_id=booking_appointment.pk,
            )

    def test_cannot_cancel_started_appointment(
        self,
        booking_patient,
        booking_appointment,
    ):
        booking_appointment.start_at = timezone.now() - timedelta(minutes=5)
        booking_appointment.end_at = timezone.now() + timedelta(minutes=25)
        booking_appointment.save(update_fields=['start_at', 'end_at'])

        with pytest.raises(ValidationError, match='начавшийся приём'):
            cancel_appointment(
                patient=booking_patient,
                appointment_id=booking_appointment.pk,
            )
