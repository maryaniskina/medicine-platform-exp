import pytest

from apps.doctors.serializers import (
    DoctorClinicSerializer,
    DoctorDetailSerializer,
    DoctorListSerializer,
    SpecializationSerializer,
)


@pytest.mark.django_db
class TestSpecializationSerializer:
    def test_serializes_public_fields(self, specialization):
        data = SpecializationSerializer(specialization).data

        assert data == {'id': specialization.pk, 'name': 'Кардиология'}

    def test_does_not_expose_internal_fields(self, specialization):
        data = SpecializationSerializer(specialization).data

        assert 'description' not in data
        assert 'is_active' not in data
        assert 'created_at' not in data
        assert 'updated_at' not in data


@pytest.mark.django_db
class TestDoctorClinicSerializer:
    def test_serializes_public_fields(
        self,
        doctor,
        clinic,
        doctor_clinic_factory,
    ):
        assignment = doctor_clinic_factory(
            doctor,
            clinic,
            price='2500.00',
            duration_minutes=45,
        )

        data = DoctorClinicSerializer(assignment).data

        assert data == {
            'clinic_id': clinic.pk,
            'clinic_name': clinic.name,
            'clinic_address': clinic.address,
            'price': '2500.00',
            'duration_minutes': 45,
        }

    def test_serializes_unknown_price(
        self,
        doctor,
        clinic,
        doctor_clinic_factory,
    ):
        assignment = doctor_clinic_factory(doctor, clinic, price=None)

        data = DoctorClinicSerializer(assignment).data

        assert data['price'] is None

    def test_does_not_expose_internal_fields(
        self,
        doctor,
        clinic,
        doctor_clinic_factory,
    ):
        assignment = doctor_clinic_factory(doctor, clinic)

        data = DoctorClinicSerializer(assignment).data

        assert 'doctor' not in data
        assert 'is_active' not in data
        assert 'created_at' not in data
        assert 'updated_at' not in data


@pytest.mark.django_db
class TestDoctorListSerializer:
    def test_serializes_public_fields(self, doctor, specialization):
        data = DoctorListSerializer(doctor).data

        assert data == {
            'id': doctor.pk,
            'first_name': 'Иван',
            'last_name': 'Иванов',
            'middle_name': 'Иванович',
            'photo_url': 'https://example.com/doctor.jpg',
            'years_of_experience': 10,
            'specializations': [
                {'id': specialization.pk, 'name': specialization.name},
            ],
        }

    def test_serializes_empty_middle_name(self, doctor):
        doctor.middle_name = ''
        doctor.save(update_fields=['middle_name'])

        data = DoctorListSerializer(doctor).data

        assert data['middle_name'] == ''

    def test_serializes_multiple_specializations(
        self,
        doctor,
        specialization_factory,
    ):
        therapy = specialization_factory(name='Терапия')
        doctor.specializations.add(therapy)

        data = DoctorListSerializer(doctor).data

        assert data['specializations'] == [
            {'id': item.pk, 'name': item.name}
            for item in doctor.specializations.order_by('name')
        ]

    def test_does_not_expose_internal_fields(self, doctor):
        data = DoctorListSerializer(doctor).data

        assert 'external_id' not in data
        assert 'description' not in data
        assert 'is_active' not in data
        assert 'created_at' not in data
        assert 'updated_at' not in data


@pytest.mark.django_db
class TestDoctorDetailSerializer:
    def test_serializes_doctor_with_clinic(
        self,
        doctor,
        clinic,
        doctor_clinic_factory,
    ):
        doctor_clinic_factory(
            doctor,
            clinic,
            price='2500.00',
            duration_minutes=45,
        )

        data = DoctorDetailSerializer(doctor).data

        assert data['id'] == doctor.pk
        assert data['description'] == 'Опытный врач-кардиолог'
        assert data['clinics'] == [
            {
                'clinic_id': clinic.pk,
                'clinic_name': clinic.name,
                'clinic_address': clinic.address,
                'price': '2500.00',
                'duration_minutes': 45,
            },
        ]

    def test_serializes_doctor_without_clinics(self, doctor):
        data = DoctorDetailSerializer(doctor).data

        assert data['clinics'] == []

    def test_excludes_inactive_assignments(
        self,
        doctor,
        clinic,
        doctor_clinic_factory,
    ):
        doctor_clinic_factory(doctor, clinic, is_active=False)

        data = DoctorDetailSerializer(doctor).data

        assert data['clinics'] == []

    def test_excludes_inactive_clinics(
        self,
        doctor,
        clinic,
        doctor_clinic_factory,
    ):
        doctor_clinic_factory(doctor, clinic)
        clinic.is_active = False
        clinic.save(update_fields=['is_active'])

        data = DoctorDetailSerializer(doctor).data

        assert data['clinics'] == []

    def test_does_not_expose_internal_fields(self, doctor):
        data = DoctorDetailSerializer(doctor).data

        assert 'external_id' not in data
        assert 'is_active' not in data
        assert 'created_at' not in data
        assert 'updated_at' not in data
