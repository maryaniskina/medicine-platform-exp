from datetime import datetime, time, timedelta
from decimal import Decimal

import pytest
from django.contrib.auth import get_user_model
from django.utils import timezone
from rest_framework.test import APIClient

from apps.accounts.models import User
from apps.appointments.models import Appointment
from apps.clinics.models import Clinic
from apps.doctors.models import Doctor, DoctorClinic, Specialization
from apps.scheduling.models import WeeklySchedule


@pytest.fixture
def user_model():
    return get_user_model()


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def csrf_client():
    return APIClient(enforce_csrf_checks=True)


@pytest.fixture
def password():
    return 'StrongPassword123!'


@pytest.fixture
def accounts_base_url():
    return '/api/accounts/'


@pytest.fixture
def user_factory(db, user_model, password):
    def create_user(**overrides):
        data = {
            'email': 'patient@example.com',
            'password': password,
            'first_name': 'Анна',
            'last_name': 'Иванова',
        }
        data.update(overrides)
        return user_model.objects.create_user(**data)

    return create_user


@pytest.fixture
def registration_data(password):
    return {
        'email': 'patient@example.com',
        'phone': '+79991234567',
        'first_name': 'Анна',
        'last_name': 'Иванова',
        'password': password,
        'password_confirm': password,
    }


@pytest.fixture
def csrf_token(csrf_client, accounts_base_url):
    response = csrf_client.get(f'{accounts_base_url}csrf/')
    assert response.status_code == 200
    return csrf_client.cookies['csrftoken'].value


@pytest.fixture
def clinics_base_url():
    return '/api/clinics/'


@pytest.fixture
def clinic_factory(db):
    def create_clinic(**overrides):
        data = {
            'external_id': 'clinic-001',
            'name': 'Клиника № 1',
            'address': 'Москва, Тверская улица, 1',
            'latitude': '55.765123',
            'longitude': '37.605678',
            'phone': '+74950000000',
            'email': 'clinic@example.com',
        }
        data.update(overrides)
        return Clinic.objects.create(**data)

    return create_clinic


@pytest.fixture
def clinic(clinic_factory):
    return clinic_factory(name='Клиника Альфа')


@pytest.fixture
def clinic_event_data():
    return {
        'external_id': 'clinic-001',
        'name': 'Клиника № 1',
        'address': 'Москва, Тверская улица, 1',
        'latitude': '55.765123',
        'longitude': '37.605678',
        'phone': '+74950000000',
        'email': 'clinic@example.com',
        'is_active': True,
    }


@pytest.fixture
def clinic_event_factory(clinic_event_data):
    def create_event(
        event_id='evt-001',
        event_type='clinic.created',
        data_overrides=None,
        **overrides,
    ):
        data = clinic_event_data.copy()
        data.update(data_overrides or {})

        return {
            'event_id': event_id,
            'event_type': event_type,
            'version': 1,
            'data': {**data, **overrides},
        }

    return create_event


@pytest.fixture
def clinic_event(clinic_event_factory):
    return clinic_event_factory()


@pytest.fixture
def booking_clinic(db):
    return Clinic.objects.create(
        external_id='test-clinic-001',
        name='Тестовая клиника',
        address='Москва, Тестовая улица, 1',
        latitude=Decimal('55.750000'),
        longitude=Decimal('37.610000'),
    )


@pytest.fixture
def booking_doctor(db):
    return Doctor.objects.create(
        external_id='test-doctor-001',
        first_name='Иван',
        last_name='Иванов',
        email='test-doctor@example.com',
    )


@pytest.fixture
def booking_doctor_clinic(booking_doctor, booking_clinic):
    return DoctorClinic.objects.create(
        doctor=booking_doctor,
        clinic=booking_clinic,
        duration_minutes=30,
    )


@pytest.fixture
def booking_patient(db):
    user_model = get_user_model()
    return user_model.objects.create_user(
        email='test-patient@example.com',
        password='StrongPassword123!',
        first_name='Анна',
        last_name='Иванова',
    )


@pytest.fixture
def another_booking_patient(db):
    user_model = get_user_model()
    return user_model.objects.create_user(
        email='another-patient@example.com',
        password='StrongPassword123!',
        first_name='Мария',
        last_name='Петрова',
    )


@pytest.fixture
def booking_doctor_user(booking_doctor):
    user_model = get_user_model()
    user = user_model.objects.create_user(
        email='doctor-user@example.com',
        password='StrongPassword123!',
        first_name='Иван',
        last_name='Иванов',
        role=user_model.Role.DOCTOR,
    )
    booking_doctor.user = user
    booking_doctor.save(update_fields=['user'])
    return user


@pytest.fixture
def booking_date():
    return timezone.localdate() + timedelta(days=7)


@pytest.fixture
def booking_schedule(booking_doctor_clinic, booking_date):
    return WeeklySchedule.objects.create(
        doctor_clinic=booking_doctor_clinic,
        weekday=booking_date.weekday(),
        start_time=time(9, 0),
        end_time=time(12, 0),
        valid_from=booking_date,
    )


@pytest.fixture
def booking_start(booking_date):
    local_timezone = timezone.get_default_timezone()
    return timezone.make_aware(
        datetime.combine(booking_date, time(10, 0)),
        local_timezone,
    )


@pytest.fixture
def booking_appointment(
    booking_patient,
    booking_doctor_clinic,
    booking_start,
):
    return Appointment.objects.create(
        patient=booking_patient,
        doctor_clinic=booking_doctor_clinic,
        start_at=booking_start,
        end_at=booking_start + timedelta(minutes=30),
        patient_comment='Первичный приём',
    )


@pytest.fixture
def doctors_base_url():
    return '/api/doctors/'


@pytest.fixture
def specialization_factory(db):
    def create_specialization(**overrides):
        data = {
            'name': 'Кардиология',
            'description': 'Диагностика заболеваний сердца',
        }
        data.update(overrides)
        return Specialization.objects.create(**data)

    return create_specialization


@pytest.fixture
def specialization(specialization_factory):
    return specialization_factory()


@pytest.fixture
def doctor_factory(db):
    def create_doctor(**overrides):
        external_id = overrides.get('external_id', 'doctor-001')
        data = {
            'external_id': external_id,
            'email': f'{external_id}@example.com',
            'first_name': 'Иван',
            'last_name': 'Иванов',
            'middle_name': 'Иванович',
            'photo_url': 'https://example.com/doctor.jpg',
            'description': 'Опытный врач-кардиолог',
            'years_of_experience': 10,
        }
        data.update(overrides)
        return Doctor.objects.create(**data)

    return create_doctor


@pytest.fixture
def doctor(doctor_factory, specialization):
    instance = doctor_factory()
    instance.specializations.add(specialization)
    return instance


@pytest.fixture
def doctor_user_factory(db):
    def create_user(**overrides):
        data = {
            'email': 'ivan@example.com',
            'password': None,
            'first_name': 'Иван',
            'last_name': 'Иванов',
            'role': User.Role.DOCTOR,
        }
        data.update(overrides)
        return User.objects.create_user(**data)

    return create_user


@pytest.fixture
def doctor_clinic_factory(db):
    def create_assignment(doctor, clinic, **overrides):
        data = {'duration_minutes': 30, 'is_active': True}
        data.update(overrides)
        return DoctorClinic.objects.create(
            doctor=doctor,
            clinic=clinic,
            **data,
        )

    return create_assignment


@pytest.fixture
def doctor_event_factory():
    def create_event(
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
        event_data.update(data or {})
        event_data.update(data_overrides)
        return {
            'event_id': event_id,
            'event_type': event_type,
            'version': 1,
            'data': event_data,
        }

    return create_event


@pytest.fixture
def doctor_event(doctor_event_factory):
    return doctor_event_factory()
