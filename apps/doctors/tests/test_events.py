from datetime import date, time
from decimal import Decimal

import pytest
from django.contrib.auth import get_user_model

from apps.doctors.models import Doctor, DoctorClinic, Specialization
from apps.doctors.services.events import (
    DoctorEventError,
    parse_doctor_event,
    process_doctor_event,
)
from apps.events.models import ProcessedMessage
from apps.scheduling.models import WeeklySchedule


@pytest.mark.django_db
class TestParseDoctorEvent:
    def test_parses_valid_event(self, doctor_event):
        event = parse_doctor_event(doctor_event)

        assert event.event_id == 'event-001'
        assert event.event_type == 'doctor.created'
        assert event.data.email == 'ivan@example.com'

    def test_rejects_missing_email(self, doctor_event_factory):
        event = doctor_event_factory()
        del event['data']['email']

        with pytest.raises(DoctorEventError):
            parse_doctor_event(event)

    def test_rejects_invalid_email(self, doctor_event_factory):
        event = doctor_event_factory(email='not-an-email')

        with pytest.raises(DoctorEventError):
            parse_doctor_event(event)

    def test_rejects_duplicate_clinics(self, doctor_event_factory):
        event = doctor_event_factory(
            clinics=[
                {'external_id': 'clinic-001'},
                {'external_id': 'clinic-001'},
            ],
        )

        with pytest.raises(DoctorEventError):
            parse_doctor_event(event)

    def test_rejects_duplicate_specializations(self, doctor_event_factory):
        event = doctor_event_factory(
            specializations=['Кардиология', 'Кардиология'],
        )

        with pytest.raises(DoctorEventError):
            parse_doctor_event(event)

    def test_rejects_invalid_experience(self, doctor_event_factory):
        event = doctor_event_factory(years_of_experience=-1)

        with pytest.raises(DoctorEventError):
            parse_doctor_event(event)


@pytest.mark.django_db
class TestProcessDoctorEvent:
    def test_creates_doctor_and_user(self, doctor_event):
        result = process_doctor_event(doctor_event)

        User = get_user_model()
        doctor = Doctor.objects.get(external_id='doctor-001')
        user = User.objects.get(email='ivan@example.com')

        assert result is True
        assert doctor.email == user.email
        assert doctor.user == user
        assert user.role == 'doctor'
        assert not user.has_usable_password()
        assert ProcessedMessage.objects.count() == 1

    def test_promotes_existing_patient_without_changing_password(
        self,
        doctor_event,
        user_factory,
    ):
        user = user_factory(
            email='ivan@example.com',
            password='Strong-test-password-123',
            role='patient',
        )
        old_password = user.password

        process_doctor_event(doctor_event)
        user.refresh_from_db()

        assert user.role == 'doctor'
        assert user.password == old_password
        assert user.check_password('Strong-test-password-123')
        assert Doctor.objects.get(external_id='doctor-001').user == user

    def test_repeated_event_is_ignored(self, doctor_event):
        assert process_doctor_event(doctor_event) is True
        assert process_doctor_event(doctor_event) is False

        assert Doctor.objects.count() == 1
        assert ProcessedMessage.objects.count() == 1

    def test_creates_specializations_and_clinic_assignments(
        self,
        doctor_event_factory,
        clinic,
    ):
        event = doctor_event_factory(
            specializations=['Кардиология', 'Терапия'],
            clinics=[
                {
                    'external_id': clinic.external_id,
                    'price': '2500.00',
                    'duration_minutes': 45,
                },
            ],
        )

        process_doctor_event(event)

        doctor = Doctor.objects.get(external_id='doctor-001')
        assignment = DoctorClinic.objects.get(doctor=doctor, clinic=clinic)

        assert set(doctor.specializations.values_list('name', flat=True)) == {
            'Кардиология',
            'Терапия',
        }
        assert assignment.price == Decimal('2500.00')
        assert assignment.duration_minutes == 45
        assert assignment.is_active is True

    def test_partial_update_preserves_existing_associations(
        self,
        doctor_event_factory,
        clinic,
    ):
        event = doctor_event_factory(
            specializations=['Кардиология'],
            clinics=[
                {
                    'external_id': clinic.external_id,
                    'price': '2500.00',
                    'duration_minutes': 45,
                },
            ],
        )
        process_doctor_event(event)
        doctor = Doctor.objects.get(external_id='doctor-001')
        specialization = doctor.specializations.get()
        assignment = DoctorClinic.objects.get(doctor=doctor)

        update = doctor_event_factory(
            event_id='event-002',
            event_type='doctor.updated',
            data={
                'external_id': 'doctor-001',
                'first_name': 'Иван',
                'last_name': 'Иванов',
                'email': 'ivan@example.com',
                'description': 'Обновлённое описание',
            },
        )
        process_doctor_event(update)
        doctor.refresh_from_db()
        assignment.refresh_from_db()

        assert doctor.description == 'Обновлённое описание'
        assert list(doctor.specializations.all()) == [specialization]
        assert assignment.is_active is True
        assert assignment.price == Decimal('2500.00')
        assert assignment.duration_minutes == 45

    def test_rejects_email_mismatch_for_existing_doctor(
        self,
        doctor_event_factory,
        user_factory,
        doctor_factory,
    ):
        user = user_factory(email='ivan@example.com')
        doctor_factory(user=user, email=user.email)
        event = doctor_event_factory(email='another@example.com')

        with pytest.raises(DoctorEventError):
            process_doctor_event(event)

        user.refresh_from_db()
        doctor = Doctor.objects.get(external_id='doctor-001')

        assert user.email == 'ivan@example.com'
        assert doctor.email == user.email
        assert doctor.user == user
        assert get_user_model().objects.count() == 1
        assert ProcessedMessage.objects.count() == 0

    def test_missing_clinic_rolls_back_all_changes(self, doctor_event_factory):
        event = doctor_event_factory(
            specializations=['Кардиология'],
            clinics=[
                {
                    'external_id': 'missing-clinic',
                    'price': '2500.00',
                    'duration_minutes': 30,
                },
            ],
        )

        with pytest.raises(DoctorEventError):
            process_doctor_event(event)

        assert Doctor.objects.count() == 0
        assert Specialization.objects.count() == 0
        assert DoctorClinic.objects.count() == 0
        assert get_user_model().objects.count() == 0
        assert ProcessedMessage.objects.count() == 0

    def test_updates_existing_doctor(self, doctor_event, doctor_event_factory):
        process_doctor_event(doctor_event)
        update = doctor_event_factory(
            event_id='event-002',
            event_type='doctor.updated',
            description='Новое описание',
            years_of_experience=12,
        )

        assert process_doctor_event(update) is True

        doctor = Doctor.objects.get(external_id='doctor-001')
        assert doctor.description == 'Новое описание'
        assert doctor.years_of_experience == 12
        assert ProcessedMessage.objects.count() == 2

    def test_rejects_schedule_without_active_clinic_assignment(
        self,
        doctor_event_factory,
    ):
        event = doctor_event_factory(
            schedules=[
                {
                    'clinic_external_id': 'clinic-001',
                    'weekday': 0,
                    'start_time': '09:00',
                    'end_time': '17:00',
                    'valid_from': '2026-01-01',
                },
            ],
        )

        with pytest.raises(DoctorEventError):
            process_doctor_event(event)

        assert Doctor.objects.count() == 0
        assert get_user_model().objects.count() == 0
        assert ProcessedMessage.objects.count() == 0

    def test_creates_schedule_for_active_assignment(
        self,
        doctor_event_factory,
        clinic,
    ):
        event = doctor_event_factory(
            clinics=[{'external_id': clinic.external_id}],
            schedules=[
                {
                    'clinic_external_id': clinic.external_id,
                    'weekday': 0,
                    'start_time': '09:00',
                    'end_time': '17:00',
                    'valid_from': '2026-01-01',
                },
            ],
        )

        process_doctor_event(event)

        schedule = WeeklySchedule.objects.get()
        assert schedule.weekday == 0
        assert schedule.start_time == time(9, 0)
        assert schedule.end_time == time(17, 0)
        assert schedule.valid_from == date(2026, 1, 1)
