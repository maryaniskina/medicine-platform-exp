from decimal import Decimal

import pytest
from django.contrib.auth import get_user_model

from apps.clinics.models import Clinic
from apps.doctors.models import Doctor, DoctorClinic, Specialization
from apps.doctors.services.events import (
    DoctorEventError,
    parse_doctor_event,
    process_doctor_event,
)
from apps.events.models import ProcessedMessage


def make_event(
    *,
    event_id='event-001',
    event_type='doctor.created',
    data=None,
    **data_overrides,
):
    event_data = {
        'external_id': 'doctor-001',
        'first_name': 'Иван',
        'last_name': 'Иванов',
        'email': 'ivan@example.com',
        'years_of_experience': 10,
    }

    if data is None:
        data = {}

    event_data.update(data)
    event_data.update(data_overrides)

    return {
        'event_id': event_id,
        'event_type': event_type,
        'version': 1,
        'data': event_data,
    }


@pytest.fixture
def clinic(db):
    return Clinic.objects.create(
        external_id='clinic-001',
        name='Клиника № 1',
        address='Москва, Тверская улица, 1',
        latitude=Decimal('55.765123'),
        longitude=Decimal('37.605678'),
    )


@pytest.mark.django_db
class TestParseDoctorEvent:
    def test_parses_valid_event(self):
        event = parse_doctor_event(make_event())

        assert event.event_id == 'event-001'
        assert event.event_type == 'doctor.created'
        assert event.data.email == 'ivan@example.com'

    def test_rejects_missing_email(self):
        event = make_event()
        del event['data']['email']

        with pytest.raises(DoctorEventError):
            parse_doctor_event(event)

    def test_rejects_invalid_email(self):
        event = make_event(email='not-an-email')

        with pytest.raises(DoctorEventError):
            parse_doctor_event(event)

    def test_rejects_duplicate_clinics(self):
        event = make_event(
            clinics=[
                {'external_id': 'clinic-001'},
                {'external_id': 'clinic-001'},
            ],
        )

        with pytest.raises(DoctorEventError):
            parse_doctor_event(event)


@pytest.mark.django_db
class TestProcessDoctorEvent:
    def test_creates_doctor_and_user(self):
        result = process_doctor_event(make_event())

        User = get_user_model()
        doctor = Doctor.objects.get(external_id='doctor-001')
        user = User.objects.get(email='ivan@example.com')

        assert result is True
        assert doctor.email == user.email
        assert doctor.user == user
        assert user.role == 'doctor'
        assert not user.has_usable_password()
        assert ProcessedMessage.objects.count() == 1

    def test_promotes_existing_patient_without_changing_password(self):
        User = get_user_model()
        user = User.objects.create_user(
            email='ivan@example.com',
            password='Strong-test-password-123',
            first_name='Иван',
            last_name='Иванов',
            role='patient',
        )
        old_password = user.password

        process_doctor_event(make_event())

        user.refresh_from_db()

        assert user.role == 'doctor'
        assert user.password == old_password
        assert user.check_password('Strong-test-password-123')

        doctor = Doctor.objects.get(external_id='doctor-001')
        assert doctor.user == user

    def test_repeated_event_is_ignored(self):
        event = make_event()

        assert process_doctor_event(event) is True
        assert process_doctor_event(event) is False

        assert Doctor.objects.count() == 1
        assert ProcessedMessage.objects.count() == 1

    def test_partial_update_preserves_existing_associations(
        self,
        clinic,
    ):
        event = make_event(
            specializations=['Кардиология'],
            clinics=[
                {
                    'external_id': 'clinic-001',
                    'price': '2500.00',
                    'duration_minutes': 45,
                },
            ],
        )
        process_doctor_event(event)

        doctor = Doctor.objects.get(external_id='doctor-001')
        specialization = doctor.specializations.get()
        assignment = DoctorClinic.objects.get(doctor=doctor)

        update = make_event(
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

    def test_rejects_email_mismatch_for_existing_doctor(self):
        User = get_user_model()
        user = User.objects.create_user(
            email='ivan@example.com',
            password=None,
            first_name='Иван',
            last_name='Иванов',
            role='doctor',
        )
        Doctor.objects.create(
            external_id='doctor-001',
            email='ivan@example.com',
            first_name='Иван',
            last_name='Иванов',
            user=user,
        )

        event = make_event(email='another@example.com')

        with pytest.raises(DoctorEventError):
            process_doctor_event(event)

        user.refresh_from_db()
        doctor = Doctor.objects.get(external_id='doctor-001')

        assert user.email == 'ivan@example.com'
        assert doctor.email == user.email
        assert doctor.user == user
        assert User.objects.count() == 1
        assert ProcessedMessage.objects.count() == 0

    def test_missing_clinic_rolls_back_all_changes(self):
        event = make_event(
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

        User = get_user_model()

        assert Doctor.objects.count() == 0
        assert Specialization.objects.count() == 0
        assert DoctorClinic.objects.count() == 0
        assert User.objects.count() == 0
        assert ProcessedMessage.objects.count() == 0
