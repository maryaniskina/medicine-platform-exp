import pytest


@pytest.mark.django_db
class TestClinicListAPI:
    def test_returns_active_clinics_without_authentication(
        self,
        api_client,
        clinics_base_url,
        clinic,
    ):
        response = api_client.get(clinics_base_url)

        assert response.status_code == 200
        assert response.data['count'] == 1
        assert response.data['results'][0]['id'] == clinic.pk

    def test_excludes_inactive_clinics(
        self,
        api_client,
        clinics_base_url,
        clinic,
    ):
        clinic.is_active = False
        clinic.save(update_fields=['is_active'])

        response = api_client.get(clinics_base_url)

        assert response.status_code == 200
        assert response.data['count'] == 0
        assert response.data['results'] == []

    def test_searches_by_name(
        self,
        api_client,
        clinics_base_url,
        clinic,
    ):
        response = api_client.get(
            clinics_base_url,
            {'search': 'Альфа'},
        )

        assert response.status_code == 200
        assert response.data['count'] == 1

    def test_searches_by_address(
        self,
        api_client,
        clinics_base_url,
        clinic,
    ):
        response = api_client.get(
            clinics_base_url,
            {'search': 'Тверская'},
        )

        assert response.status_code == 200
        assert response.data['count'] == 1

    def test_search_is_case_insensitive(
        self,
        api_client,
        clinics_base_url,
        clinic,
    ):
        response = api_client.get(
            clinics_base_url,
            {'search': 'альфа'},
        )

        assert response.status_code == 200
        assert response.data['count'] == 1

    def test_search_without_matches_returns_empty_list(
        self,
        api_client,
        clinics_base_url,
        clinic,
    ):
        response = api_client.get(
            clinics_base_url,
            {'search': 'Несуществующая'},
        )

        assert response.status_code == 200
        assert response.data['count'] == 0

    def test_search_ignores_surrounding_whitespace(
        self,
        api_client,
        clinics_base_url,
        clinic,
    ):
        response = api_client.get(
            clinics_base_url,
            {'search': ' Альфа '},
        )

        assert response.status_code == 200
        assert response.data['count'] == 1

    def test_results_are_ordered_by_name(
        self,
        api_client,
        clinics_base_url,
        clinic,
        clinic_factory,
    ):
        clinic_factory(
            external_id='clinic-002',
            name='Клиника Бета',
            address='Москва, другой адрес',
        )

        response = api_client.get(clinics_base_url)

        assert response.status_code == 200
        names = [item['name'] for item in response.data['results']]
        assert names == ['Клиника Альфа', 'Клиника Бета']

    def test_response_does_not_expose_internal_fields(
        self,
        api_client,
        clinics_base_url,
        clinic,
    ):
        response = api_client.get(clinics_base_url)

        item = response.data['results'][0]

        assert 'external_id' not in item
        assert 'is_active' not in item
        assert 'created_at' not in item
        assert 'updated_at' not in item

    def test_supports_pagination(
        self,
        api_client,
        clinics_base_url,
        clinic,
        clinic_factory,
    ):
        for number in range(20):
            clinic_factory(
                external_id=f'clinic-{number + 100}',
                name=f'Клиника {number:02}',
            )

        response = api_client.get(clinics_base_url)

        assert response.status_code == 200
        assert response.data['count'] == 21
        assert len(response.data['results']) == 20
        assert response.data['next'] is not None
        assert response.data['previous'] is None

    def test_returns_second_page(
        self,
        api_client,
        clinics_base_url,
        clinic,
        clinic_factory,
    ):
        for number in range(20):
            clinic_factory(
                external_id=f'clinic-{number + 100}',
                name=f'Клиника {number:02}',
            )

        response = api_client.get(clinics_base_url, {'page': 2})

        assert response.status_code == 200
        assert len(response.data['results']) == 1
        assert response.data['next'] is None
        assert response.data['previous'] is not None


@pytest.mark.django_db
class TestClinicDetailAPI:
    def test_returns_clinic_without_authentication(
        self,
        api_client,
        clinics_base_url,
        clinic,
    ):
        response = api_client.get(f'{clinics_base_url}{clinic.pk}/')

        assert response.status_code == 200
        assert response.data['id'] == clinic.pk
        assert response.data['name'] == clinic.name
        assert response.data['address'] == clinic.address

    def test_returns_404_for_missing_clinic(
        self,
        api_client,
        clinics_base_url,
    ):
        response = api_client.get(f'{clinics_base_url}999999/')

        assert response.status_code == 404

    def test_returns_404_for_inactive_clinic(
        self,
        api_client,
        clinics_base_url,
        clinic,
    ):
        clinic.is_active = False
        clinic.save(update_fields=['is_active'])

        response = api_client.get(f'{clinics_base_url}{clinic.pk}/')

        assert response.status_code == 404

    def test_does_not_expose_external_id(
        self,
        api_client,
        clinics_base_url,
        clinic,
    ):
        response = api_client.get(f'{clinics_base_url}{clinic.pk}/')

        assert response.status_code == 200
        assert 'external_id' not in response.data

    def test_invalid_primary_key_returns_404(
        self,
        api_client,
        clinics_base_url,
    ):
        response = api_client.get(f'{clinics_base_url}not-an-id/')

        assert response.status_code == 404
