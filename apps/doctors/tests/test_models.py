from decimal import Decimal

import pytest
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from django.db.models.deletion import ProtectedError

from apps.clinics.models import Clinic
from apps.doctors.models import Doctor, DoctorClinic, Specialization


@pytest.mark.django_db
class TestSpecializationModel:
    def test_create_specialization(self):
        specialization = Specialization.objects.create(
            name='Кардиология',
            description='Диагностика и лечение заболеваний сердца',
        )

        assert specialization.pk is not None
        assert specialization.name == 'Кардиология'
        assert str(specialization) == 'Кардиология'
        assert specialization.is_active is True

    def test_name_must_be_unique(self):
        Specialization.objects.create(name='Кардиология')

        with pytest.raises(IntegrityError):
            with transaction.atomic():
                Specialization.objects.create(name='Кардиология')

    def test_default_ordering_is_by_name(self):
        Specialization.objects.create(name='Терапия')
        Specialization.objects.create(name='Кардиология')

        names = list(Specialization.objects.values_list('name', flat=True))

        assert names == ['Кардиология', 'Терапия']


@pytest.mark.django_db
class TestDoctorModel:
    def create_doctor(self, **overrides):
        external_id = overrides.get('external_id', 'doctor-001')
        data = {
            'external_id': external_id,
            'email': f'{external_id}@example.com',
            'first_name': 'Иван',
            'last_name': 'Иванов',
            'middle_name': 'Иванович',
            'years_of_experience': 10,
        }
        data.update(overrides)

        return Doctor.objects.create(**data)

    def create_user(self, **overrides):
        User = get_user_model()
        data = {
            'email': 'ivan@example.com',
            'password': None,
            'first_name': 'Иван',
            'last_name': 'Иванов',
            'role': 'doctor',
        }
        data.update(overrides)

        return User.objects.create_user(**data)

    def test_create_doctor(self):
        doctor = self.create_doctor()

        assert doctor.pk is not None
        assert doctor.external_id == 'doctor-001'
        assert doctor.email == 'doctor-001@example.com'
        assert doctor.first_name == 'Иван'
        assert doctor.last_name == 'Иванов'
        assert doctor.middle_name == 'Иванович'
        assert doctor.years_of_experience == 10
        assert doctor.user is None
        assert str(doctor) == 'Иванов Иван Иванович'

    def test_doctor_without_middle_name(self):
        doctor = self.create_doctor(middle_name='')

        assert str(doctor) == 'Иванов Иван'

    def test_active_by_default(self):
        doctor = self.create_doctor()

        assert doctor.is_active is True

    def test_external_id_must_be_unique(self):
        self.create_doctor()

        with pytest.raises(IntegrityError):
            with transaction.atomic():
                self.create_doctor(
                    external_id='doctor-001',
                    first_name='Пётр',
                )

    def test_email_must_be_unique(self):
        self.create_doctor(email='ivan@example.com')

        with pytest.raises(IntegrityError):
            with transaction.atomic():
                self.create_doctor(
                    external_id='doctor-002',
                    email='ivan@example.com',
                )

    @pytest.mark.parametrize('years', [0, 1, 50, 32767])
    def test_valid_years_of_experience(self, years):
        doctor = self.create_doctor(years_of_experience=years)

        doctor.full_clean()

    def test_doctor_can_have_multiple_specializations(self):
        doctor = self.create_doctor()
        cardiology = Specialization.objects.create(name='Кардиология')
        therapy = Specialization.objects.create(name='Терапия')

        doctor.specializations.add(cardiology, therapy)

        assert set(doctor.specializations.all()) == {
            cardiology,
            therapy,
        }

    def test_default_ordering_is_by_name(self):
        self.create_doctor(
            external_id='doctor-002',
            first_name='Пётр',
            last_name='Сидоров',
        )
        self.create_doctor(
            external_id='doctor-003',
            first_name='Анна',
            last_name='Иванова',
        )
        self.create_doctor(
            external_id='doctor-001',
            first_name='Иван',
            last_name='Иванов',
        )

        doctors = list(Doctor.objects.values_list('last_name', flat=True))

        assert doctors == ['Иванов', 'Иванова', 'Сидоров']

    def test_doctor_can_be_linked_to_user(self):
        user = self.create_user()

        doctor = self.create_doctor(
            user=user,
            email=user.email,
        )

        assert doctor.user == user
        assert user.doctor_profile == doctor

    def test_user_can_be_linked_to_only_one_doctor(self):
        user = self.create_user()

        self.create_doctor(
            external_id='doctor-001',
            user=user,
            email=user.email,
        )

        with pytest.raises(IntegrityError):
            with transaction.atomic():
                self.create_doctor(
                    external_id='doctor-002',
                    user=user,
                    email='another@example.com',
                )

    def test_user_cannot_be_deleted_while_linked_to_doctor(self):
        user = self.create_user()

        self.create_doctor(
            user=user,
            email=user.email,
        )

        with pytest.raises(ProtectedError):
            user.delete()


@pytest.mark.django_db
class TestDoctorClinicModel:
    def create_clinic(self, **overrides):
        data = {
            'external_id': 'clinic-001',
            'name': 'Клиника № 1',
            'address': 'Москва, Тверская улица, 1',
            'latitude': '55.765123',
            'longitude': '37.605678',
        }
        data.update(overrides)

        return Clinic.objects.create(**data)

    def create_doctor(self, **overrides):
        external_id = overrides.get('external_id', 'doctor-001')
        data = {
            'external_id': external_id,
            'email': f'{external_id}@example.com',
            'first_name': 'Иван',
            'last_name': 'Иванов',
        }
        data.update(overrides)

        return Doctor.objects.create(**data)

    def test_create_doctor_clinic(self):
        doctor = self.create_doctor()
        clinic = self.create_clinic()

        assignment = DoctorClinic.objects.create(
            doctor=doctor,
            clinic=clinic,
            price='2500.00',
            duration_minutes=45,
        )

        assert assignment.pk is not None
        assert Decimal(assignment.price) == Decimal('2500.00')
        assert assignment.duration_minutes == 45
        assert assignment.is_active is True
        assert str(assignment) == 'Иванов Иван — Клиника № 1'

    def test_price_can_be_unknown(self):
        doctor = self.create_doctor()
        clinic = self.create_clinic()

        assignment = DoctorClinic.objects.create(
            doctor=doctor,
            clinic=clinic,
            price=None,
        )

        assert assignment.price is None

    def test_price_cannot_be_negative(self):
        doctor = self.create_doctor()
        clinic = self.create_clinic()
        assignment = DoctorClinic(
            doctor=doctor,
            clinic=clinic,
            price='-1.00',
        )

        with pytest.raises(ValidationError):
            assignment.full_clean()

    @pytest.mark.parametrize('duration', [5, 30, 240])
    def test_valid_duration(self, duration):
        doctor = self.create_doctor()
        clinic = self.create_clinic()

        assignment = DoctorClinic(
            doctor=doctor,
            clinic=clinic,
            duration_minutes=duration,
        )

        assignment.full_clean()

    @pytest.mark.parametrize('duration', [4, 241])
    def test_invalid_duration(self, duration):
        doctor = self.create_doctor()
        clinic = self.create_clinic()

        assignment = DoctorClinic(
            doctor=doctor,
            clinic=clinic,
            duration_minutes=duration,
        )

        with pytest.raises(ValidationError):
            assignment.full_clean()

    def test_doctor_clinic_pair_must_be_unique(self):
        doctor = self.create_doctor()
        clinic = self.create_clinic()

        DoctorClinic.objects.create(doctor=doctor, clinic=clinic)

        with pytest.raises(IntegrityError):
            with transaction.atomic():
                DoctorClinic.objects.create(
                    doctor=doctor,
                    clinic=clinic,
                )

    def test_doctor_can_work_in_multiple_clinics(self):
        doctor = self.create_doctor()
        first_clinic = self.create_clinic()
        second_clinic = self.create_clinic(
            external_id='clinic-002',
            name='Клиника № 2',
        )

        DoctorClinic.objects.create(
            doctor=doctor,
            clinic=first_clinic,
            price='2000.00',
        )
        DoctorClinic.objects.create(
            doctor=doctor,
            clinic=second_clinic,
            price='3000.00',
        )

        assert doctor.clinics.count() == 2
        assert doctor.clinic_assignments.count() == 2

    def test_clinic_cannot_be_deleted_while_doctors_are_assigned(self):
        doctor = self.create_doctor()
        clinic = self.create_clinic()

        DoctorClinic.objects.create(doctor=doctor, clinic=clinic)

        with pytest.raises(ProtectedError):
            clinic.delete()

    def test_doctor_can_be_deleted_with_assignments(self):
        doctor = self.create_doctor()
        clinic = self.create_clinic()

        DoctorClinic.objects.create(doctor=doctor, clinic=clinic)

        doctor.delete()

        assert not DoctorClinic.objects.filter(clinic=clinic).exists()
