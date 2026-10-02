from decimal import Decimal

import pytest
from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from django.db.models.deletion import ProtectedError

from apps.doctors.models import Doctor, DoctorClinic, Specialization


@pytest.mark.django_db
class TestSpecializationModel:
    def test_create_specialization(self, specialization_factory):
        specialization = specialization_factory()

        assert specialization.pk is not None
        assert specialization.name == 'Кардиология'
        assert str(specialization) == 'Кардиология'
        assert specialization.is_active is True

    def test_name_must_be_unique(self, specialization_factory):
        specialization_factory(name='Кардиология')

        with pytest.raises(IntegrityError), transaction.atomic():
            specialization_factory(name='Кардиология')

    def test_default_ordering_is_by_name(self, specialization_factory):
        specialization_factory(name='Терапия')
        specialization_factory(name='Кардиология')

        names = list(Specialization.objects.values_list('name', flat=True))

        assert names == ['Кардиология', 'Терапия']


@pytest.mark.django_db
class TestDoctorModel:
    def test_create_doctor(self, doctor_factory):
        doctor = doctor_factory()

        assert doctor.pk is not None
        assert doctor.external_id == 'doctor-001'
        assert doctor.email == 'doctor-001@example.com'
        assert doctor.first_name == 'Иван'
        assert doctor.last_name == 'Иванов'
        assert doctor.middle_name == 'Иванович'
        assert doctor.years_of_experience == 10
        assert doctor.user is None
        assert str(doctor) == 'Иванов Иван Иванович'

    def test_doctor_without_middle_name(self, doctor_factory):
        doctor = doctor_factory(middle_name='')

        assert str(doctor) == 'Иванов Иван'

    def test_active_by_default(self, doctor_factory):
        doctor = doctor_factory()

        assert doctor.is_active is True

    def test_external_id_must_be_unique(self, doctor_factory):
        doctor_factory(external_id='doctor-001')

        with pytest.raises(IntegrityError), transaction.atomic():
            doctor_factory(external_id='doctor-001', first_name='Пётр')

    def test_email_must_be_unique(self, doctor_factory):
        doctor_factory(external_id='doctor-001', email='ivan@example.com')

        with pytest.raises(IntegrityError), transaction.atomic():
            doctor_factory(
                external_id='doctor-002',
                email='ivan@example.com',
            )

    @pytest.mark.parametrize('years', [0, 1, 50, 32767])
    def test_valid_years_of_experience(self, doctor_factory, years):
        doctor = doctor_factory(years_of_experience=years)

        doctor.full_clean()

    def test_doctor_can_have_multiple_specializations(
        self,
        doctor_factory,
        specialization_factory,
    ):
        doctor = doctor_factory()
        cardiology = specialization_factory(name='Кардиология')
        therapy = specialization_factory(name='Терапия')

        doctor.specializations.add(cardiology, therapy)

        assert set(doctor.specializations.all()) == {cardiology, therapy}

    def test_default_ordering_is_by_name(self, doctor_factory):
        doctor_factory(
            external_id='doctor-002',
            first_name='Пётр',
            last_name='Сидоров',
        )
        doctor_factory(
            external_id='doctor-003',
            first_name='Анна',
            last_name='Иванова',
        )
        doctor_factory(
            external_id='doctor-001',
            first_name='Иван',
            last_name='Иванов',
        )

        doctors = list(Doctor.objects.values_list('last_name', flat=True))

        assert doctors == ['Иванов', 'Иванова', 'Сидоров']

    def test_doctor_can_be_linked_to_user(self, doctor_factory, user_factory):
        user = user_factory()
        doctor = doctor_factory(user=user, email=user.email)

        assert doctor.user == user
        assert user.doctor_profile == doctor

    def test_user_can_be_linked_to_only_one_doctor(
        self,
        doctor_factory,
        user_factory,
    ):
        user = user_factory()
        doctor_factory(
            external_id='doctor-001',
            user=user,
            email=user.email,
        )

        with pytest.raises(IntegrityError), transaction.atomic():
            doctor_factory(
                external_id='doctor-002',
                user=user,
                email='another@example.com',
            )

    def test_user_cannot_be_deleted_while_linked_to_doctor(
        self,
        doctor_factory,
        user_factory,
    ):
        user = user_factory()
        doctor_factory(user=user, email=user.email)

        with pytest.raises(ProtectedError):
            user.delete()


@pytest.mark.django_db
class TestDoctorClinicModel:
    def test_create_doctor_clinic(
        self,
        doctor_factory,
        clinic_factory,
        doctor_clinic_factory,
    ):
        doctor = doctor_factory()
        clinic = clinic_factory()
        assignment = doctor_clinic_factory(
            doctor,
            clinic,
            price='2500.00',
            duration_minutes=45,
        )

        assert assignment.pk is not None
        assert Decimal(assignment.price) == Decimal('2500.00')
        assert assignment.duration_minutes == 45
        assert assignment.is_active is True
        assert str(assignment) == 'Иванов Иван Иванович — Клиника № 1'

    def test_price_can_be_unknown(
        self,
        doctor_factory,
        clinic_factory,
        doctor_clinic_factory,
    ):
        doctor = doctor_factory()
        clinic = clinic_factory()
        assignment = doctor_clinic_factory(doctor, clinic, price=None)

        assert assignment.price is None

    def test_price_cannot_be_negative(
        self,
        doctor_factory,
        clinic_factory,
    ):
        assignment = DoctorClinic(
            doctor=doctor_factory(),
            clinic=clinic_factory(),
            price='-1.00',
        )

        with pytest.raises(ValidationError):
            assignment.full_clean()

    @pytest.mark.parametrize('duration', [5, 30, 240])
    def test_valid_duration(
        self,
        doctor_factory,
        clinic_factory,
        duration,
    ):
        assignment = DoctorClinic(
            doctor=doctor_factory(),
            clinic=clinic_factory(),
            duration_minutes=duration,
        )

        assignment.full_clean()

    @pytest.mark.parametrize('duration', [4, 241])
    def test_invalid_duration(
        self,
        doctor_factory,
        clinic_factory,
        duration,
    ):
        assignment = DoctorClinic(
            doctor=doctor_factory(),
            clinic=clinic_factory(),
            duration_minutes=duration,
        )

        with pytest.raises(ValidationError):
            assignment.full_clean()

    def test_doctor_clinic_pair_must_be_unique(
        self,
        doctor_factory,
        clinic_factory,
        doctor_clinic_factory,
    ):
        doctor = doctor_factory()
        clinic = clinic_factory()
        doctor_clinic_factory(doctor, clinic)

        with pytest.raises(IntegrityError), transaction.atomic():
            doctor_clinic_factory(doctor, clinic)

    def test_doctor_can_work_in_multiple_clinics(
        self,
        doctor_factory,
        clinic_factory,
        doctor_clinic_factory,
    ):
        doctor = doctor_factory()
        first_clinic = clinic_factory()
        second_clinic = clinic_factory(
            external_id='clinic-002',
            name='Клиника № 2',
        )
        doctor_clinic_factory(doctor, first_clinic, price='2000.00')
        doctor_clinic_factory(doctor, second_clinic, price='3000.00')

        assert doctor.clinics.count() == 2
        assert doctor.clinic_assignments.count() == 2

    def test_clinic_cannot_be_deleted_while_doctors_are_assigned(
        self,
        doctor_factory,
        clinic_factory,
        doctor_clinic_factory,
    ):
        doctor = doctor_factory()
        clinic = clinic_factory()
        doctor_clinic_factory(doctor, clinic)

        with pytest.raises(ProtectedError):
            clinic.delete()

    def test_doctor_can_be_deleted_with_assignments(
        self,
        doctor_factory,
        clinic_factory,
        doctor_clinic_factory,
    ):
        doctor = doctor_factory()
        clinic = clinic_factory()
        doctor_clinic_factory(doctor, clinic)

        doctor.delete()

        assert not DoctorClinic.objects.filter(clinic=clinic).exists()
