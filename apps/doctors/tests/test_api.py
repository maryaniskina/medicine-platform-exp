import pytest
from rest_framework.test import APIClient

from apps.clinics.models import Clinic
from apps.doctors.models import Doctor, DoctorClinic, Specialization

BASE_URL = '/api/doctors/'


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def clinic(db):
    return Clinic.objects.create(
        external_id='clinic-001',
        name='Клиника Альфа',
        address='Москва, Тверская улица, 1',
        latitude='55.765123',
        longitude='37.605678',
    )


@pytest.fixture
def specialization(db):
    return Specialization.objects.create(name='Кардиология')


@pytest.fixture
def doctor(db, specialization):
    doctor = Doctor.objects.create(
        external_id='doctor-001',
        first_name='Иван',
        last_name='Иванов',
        middle_name='Иванович',
        description='Врач-кардиолог',
        years_of_experience=10,
    )
    doctor.specializations.add(specialization)
    return doctor


@pytest.mark.django_db
class TestDoctorListAPI:
    def test_returns_active_doctors_without_authentication(
        self,
        api_client,
        doctor,
    ):
        response = api_client.get(BASE_URL)

        assert response.status_code == 200
        assert response.data['count'] == 1
        assert response.data['results'][0]['id'] == doctor.pk

    def test_excludes_inactive_doctors(self, api_client, doctor):
        doctor.is_active = False
        doctor.save(update_fields=['is_active'])

        response = api_client.get(BASE_URL)

        assert response.status_code == 200
        assert response.data['count'] == 0
        assert response.data['results'] == []

    def test_searches_by_first_name(self, api_client, doctor):
        response = api_client.get(BASE_URL, {'search': 'Иван'})

        assert response.status_code == 200
        assert response.data['count'] == 1

    def test_searches_by_last_name(self, api_client, doctor):
        response = api_client.get(BASE_URL, {'search': 'Иванов'})

        assert response.status_code == 200
        assert response.data['count'] == 1

    def test_search_is_case_insensitive(self, api_client, doctor):
        response = api_client.get(BASE_URL, {'search': 'иван'})

        assert response.status_code == 200
        assert response.data['count'] == 1

    def test_filters_by_specialization(
        self,
        api_client,
        doctor,
        specialization,
    ):
        response = api_client.get(
            BASE_URL,
            {'specialization': specialization.pk},
        )

        assert response.status_code == 200
        assert response.data['count'] == 1

    def test_filters_by_clinic(
        self,
        api_client,
        doctor,
        clinic,
    ):
        DoctorClinic.objects.create(doctor=doctor, clinic=clinic)

        response = api_client.get(BASE_URL, {'clinic': clinic.pk})

        assert response.status_code == 200
        assert response.data['count'] == 1

    def test_excludes_doctors_with_inactive_clinic_assignments(
        self,
        api_client,
        doctor,
        clinic,
    ):
        DoctorClinic.objects.create(
            doctor=doctor,
            clinic=clinic,
            is_active=False,
        )

        response = api_client.get(BASE_URL, {'clinic': clinic.pk})

        assert response.status_code == 200
        assert response.data['count'] == 0

    def test_does_not_expose_internal_fields(self, api_client, doctor):
        response = api_client.get(BASE_URL)

        item = response.data['results'][0]

        assert 'external_id' not in item
        assert 'is_active' not in item
        assert 'created_at' not in item
        assert 'updated_at' not in item

    def test_returns_specializations(self, api_client, doctor):
        response = api_client.get(BASE_URL)

        item = response.data['results'][0]

        assert item['specializations'] == [
            {
                'id': doctor.specializations.get().pk,
                'name': 'Кардиология',
            },
        ]


@pytest.mark.django_db
class TestDoctorDetailAPI:
    def test_returns_doctor_details(
        self,
        api_client,
        doctor,
        clinic,
    ):
        DoctorClinic.objects.create(
            doctor=doctor,
            clinic=clinic,
            price='2500.00',
            duration_minutes=45,
        )

        response = api_client.get(f'{BASE_URL}{doctor.pk}/')

        assert response.status_code == 200
        assert response.data['id'] == doctor.pk
        assert response.data['first_name'] == 'Иван'
        assert response.data['last_name'] == 'Иванов'
        assert response.data['description'] == 'Врач-кардиолог'
        assert response.data['clinics'] == [
            {
                'clinic_id': clinic.pk,
                'clinic_name': 'Клиника Альфа',
                'clinic_address': 'Москва, Тверская улица, 1',
                'price': '2500.00',
                'duration_minutes': 45,
            },
        ]

    def test_returns_empty_clinics_when_doctor_has_no_assignments(
        self,
        api_client,
        doctor,
    ):
        response = api_client.get(f'{BASE_URL}{doctor.pk}/')

        assert response.status_code == 200
        assert response.data['clinics'] == []

    def test_excludes_inactive_clinics_from_details(
        self,
        api_client,
        doctor,
        clinic,
    ):
        DoctorClinic.objects.create(doctor=doctor, clinic=clinic)
        clinic.is_active = False
        clinic.save(update_fields=['is_active'])

        response = api_client.get(f'{BASE_URL}{doctor.pk}/')

        assert response.status_code == 200
        assert response.data['clinics'] == []

    def test_returns_404_for_missing_doctor(self, api_client):
        response = api_client.get(f'{BASE_URL}999999/')

        assert response.status_code == 404

    def test_returns_404_for_inactive_doctor(self, api_client, doctor):
        doctor.is_active = False
        doctor.save(update_fields=['is_active'])

        response = api_client.get(f'{BASE_URL}{doctor.pk}/')

        assert response.status_code == 404

    def test_invalid_primary_key_returns_404(self, api_client):
        response = api_client.get(f'{BASE_URL}not-an-id/')

        assert response.status_code == 404
