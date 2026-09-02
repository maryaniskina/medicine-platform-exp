import pytest


@pytest.mark.django_db
class TestRegistrationAPI:
    def test_register_success(self, api_client, accounts_base_url, registration_data):
        response = api_client.post(
            f'{accounts_base_url}register/',
            registration_data,
            format='json',
        )

        assert response.status_code == 201
        assert response.data['email'] == registration_data['email']
        assert 'password' not in response.data

    def test_register_duplicate_email(
        self,
        api_client,
        accounts_base_url,
        registration_data,
        user_factory,
    ):
        user_factory(email=registration_data['email'])

        response = api_client.post(
            f'{accounts_base_url}register/',
            registration_data,
            format='json',
        )

        assert response.status_code == 400

    def test_register_password_mismatch(
        self,
        api_client,
        accounts_base_url,
        registration_data,
    ):
        registration_data['password_confirm'] = 'AnotherPassword123!'

        response = api_client.post(
            f'{accounts_base_url}register/',
            registration_data,
            format='json',
        )

        assert response.status_code == 400


@pytest.mark.django_db
class TestLoginAPI:
    def test_login_success(
        self,
        api_client,
        accounts_base_url,
        user_factory,
        password,
    ):
        user = user_factory()

        response = api_client.post(
            f'{accounts_base_url}login/',
            {'email': user.email, 'password': password},
            format='json',
        )

        assert response.status_code == 200

    def test_login_invalid_password(
        self,
        api_client,
        accounts_base_url,
        user_factory,
    ):
        user = user_factory()

        response = api_client.post(
            f'{accounts_base_url}login/',
            {'email': user.email, 'password': 'WrongPassword123!'},
            format='json',
        )

        assert response.status_code == 400

    def test_logout_authenticated_user(
        self,
        api_client,
        accounts_base_url,
        user_factory,
        password,
    ):
        user = user_factory()
        api_client.force_login(user)

        response = api_client.post(f'{accounts_base_url}logout/')

        assert response.status_code in (200, 204)


@pytest.mark.django_db
class TestCSRFAPI:
    def test_csrf_endpoint_returns_token(self, csrf_client, accounts_base_url):
        response = csrf_client.get(f'{accounts_base_url}csrf/')

        assert response.status_code == 200
        assert 'csrftoken' in csrf_client.cookies

    def test_login_requires_csrf_token(
        self,
        csrf_client,
        accounts_base_url,
        user_factory,
        password,
    ):
        user = user_factory()

        response = csrf_client.post(
            f'{accounts_base_url}login/',
            {'email': user.email, 'password': password},
            format='json',
        )

        assert response.status_code == 403

    def test_login_with_csrf_token(
        self,
        csrf_client,
        accounts_base_url,
        csrf_token,
        user_factory,
        password,
    ):
        user = user_factory()

        response = csrf_client.post(
            f'{accounts_base_url}login/',
            {'email': user.email, 'password': password},
            format='json',
            HTTP_X_CSRFTOKEN=csrf_token,
        )

        assert response.status_code == 200

    def test_logout_requires_authentication(self, api_client, accounts_base_url):
        response = api_client.post(f'{accounts_base_url}logout/')

        assert response.status_code in (401, 403)
