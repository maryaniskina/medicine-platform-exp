import pytest

@pytest.mark.django_db
class TestDoctorListAPI:
    def test_returns_active_doctors_without_authentication(
        self,
        api_client,
        doctors_base_url,
        doctor,
    ):
        response = api_client.get(doctors_base_url)

        assert response.status_code == 200
        assert response.data['count'] == 1
        assert response.data['results'][0]['id'] == doctor.pk

    def test_excludes_inactive_doctors(
        self,
        api_client,
        doctors_base_url,
        doctor,
    ):
        doctor.is_active = False
        doctor.save(update_fields=['is_active'])

        response = api_client.get(doctors_base_url)

        assert response.status_code == 200
        assert response.data['count'] == 0
        assert response.data['results'] == []

    @pytest.mark.parametrize('search', ['Иван', 'Иванов', 'иван', 'Иванович'])
    def test_searches_by_name_case_insensitively(
        self,
        api_client,
        doctors_base_url,
        doctor,
        search,
    ):
        response = api_client.get(doctors_base_url, {'search': search})

        assert response.status_code == 200
        assert response.data['count'] == 1

    def test_filters_by_specialization(
        self,
        api_client,
        doctors_base_url,
        doctor,
        specialization,
    ):
        response = api_client.get(
            doctors_base_url,
            {'specialization': specialization.pk},
        )

        assert response.status_code == 200
        assert response.data['count'] == 1

    def test_filters_by_clinic(
        self,
        api_client,
        doctors_base_url,
        doctor,
        clinic,
        doctor_clinic_factory,
    ):
        doctor_clinic_factory(doctor, clinic)

        response = api_client.get(doctors_base_url, {'clinic': clinic.pk})

        assert response.status_code == 200
        assert response.data['count'] == 1

    def test_excludes_doctors_with_inactive_clinic_assignments(
        self,
        api_client,
        doctors_base_url,
        doctor,
        clinic,
        doctor_clinic_factory,
    ):
        doctor_clinic_factory(doctor, clinic, is_active=False)

        response = api_client.get(doctors_base_url, {'clinic': clinic.pk})

        assert response.status_code == 200
        assert response.data['count'] == 0

    def test_excludes_doctors_with_inactive_clinics(
        self,
        api_client,
        doctors_base_url,
        doctor,
        clinic,
        doctor_clinic_factory,
    ):
        doctor_clinic_factory(doctor, clinic)
        clinic.is_active = False
        clinic.save(update_fields=['is_active'])

        response = api_client.get(doctors_base_url, {'clinic': clinic.pk})

        assert response.status_code == 200
        assert response.data['count'] == 0

    def test_does_not_expose_internal_fields(
        self,
        api_client,
        doctors_base_url,
        doctor,
    ):
        response = api_client.get(doctors_base_url)
        item = response.data['results'][0]

        assert 'external_id' not in item
        assert 'is_active' not in item
        assert 'created_at' not in item
        assert 'updated_at' not in item

    def test_returns_specializations(
        self,
        api_client,
        doctors_base_url,
        doctor,
        specialization,
    ):
        response = api_client.get(doctors_base_url)
        item = response.data['results'][0]

        assert item['specializations'] == [
            {'id': specialization.pk, 'name': specialization.name},
        ]


@pytest.mark.django_db
class TestDoctorDetailAPI:
    def test_returns_doctor_details(
        self,
        api_client,
        doctors_base_url,
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

        response = api_client.get(f'{doctors_base_url}{doctor.pk}/')

        assert response.status_code == 200
        assert response.data['id'] == doctor.pk
        assert response.data['first_name'] == 'Иван'
        assert response.data['last_name'] == 'Иванов'
        assert response.data['description'] == 'Опытный врач-кардиолог'
        assert response.data['clinics'] == [
            {
                'clinic_id': clinic.pk,
                'clinic_name': clinic.name,
                'clinic_address': clinic.address,
                'price': '2500.00',
                'duration_minutes': 45,
            },
        ]

    def test_returns_empty_clinics_when_doctor_has_no_assignments(
        self,
        api_client,
        doctors_base_url,
        doctor,
    ):
        response = api_client.get(f'{doctors_base_url}{doctor.pk}/')

        assert response.status_code == 200
        assert response.data['clinics'] == []

    def test_excludes_inactive_assignments(
        self,
        api_client,
        doctors_base_url,
        doctor,
        clinic,
        doctor_clinic_factory,
    ):
        doctor_clinic_factory(doctor, clinic, is_active=False)

        response = api_client.get(f'{doctors_base_url}{doctor.pk}/')

        assert response.status_code == 200
        assert response.data['clinics'] == []

    def test_excludes_inactive_clinics(
        self,
        api_client,
        doctors_base_url,
        doctor,
        clinic,
        doctor_clinic_factory,
    ):
        doctor_clinic_factory(doctor, clinic)
        clinic.is_active = False
        clinic.save(update_fields=['is_active'])

        response = api_client.get(f'{doctors_base_url}{doctor.pk}/')

        assert response.status_code == 200
        assert response.data['clinics'] == []

    def test_returns_404_for_missing_doctor(
        self,
        api_client,
        doctors_base_url,
    ):
        response = api_client.get(f'{doctors_base_url}999999/')

        assert response.status_code == 404

    def test_returns_404_for_inactive_doctor(
        self,
        api_client,
        doctors_base_url,
        doctor,
    ):
        doctor.is_active = False
        doctor.save(update_fields=['is_active'])

        response = api_client.get(f'{doctors_base_url}{doctor.pk}/')

        assert response.status_code == 404

    def test_invalid_primary_key_returns_404(
        self,
        api_client,
        doctors_base_url,
    ):
        response = api_client.get(f'{doctors_base_url}not-an-id/')

        assert response.status_code == 404
