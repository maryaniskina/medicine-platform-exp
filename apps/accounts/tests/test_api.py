import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient

User = get_user_model()

BASE_URL = '/api/accounts/'
PASSWORD = 'StrongPassword123!'


@pytest.mark.django_db
class TestAccountsAPI:
    def setup_method(self):
        self.client = APIClient()

    def create_user(self, **overrides):
        data = {
            'email': 'patient@example.com',
            'password': PASSWORD,
            'first_name': 'Анна',
            'last_name': 'Иванова',
        }
        data.update(overrides)
        return User.objects.create_user(**data)

    def registration_data(self, **overrides):
        data = {
            'email': 'patient@example.com',
            'phone': '+79991234567',
            'first_name': 'Анна',
            'last_name': 'Иванова',
            'password': PASSWORD,
            'password_confirm': PASSWORD,
        }
        data.update(overrides)
        return data

    def login(self, email='patient@example.com', password=PASSWORD):
        return self.client.post(
            f'{BASE_URL}login/',
            {'email': email, 'password': password},
            format='json',
        )

    def test_register_creates_patient(self):
        response = self.client.post(
            f'{BASE_URL}register/',
            self.registration_data(),
            format='json',
        )

        assert response.status_code == 201

        user = User.objects.get(email='patient@example.com')
        assert user.role == User.Role.PATIENT
        assert user.check_password(PASSWORD)

    def test_register_returns_phone(self):
        response = self.client.post(
            f'{BASE_URL}register/',
            self.registration_data(),
            format='json',
        )

        assert response.status_code == 201
        assert response.data['phone'] == '+79991234567'

    def test_register_rejects_duplicate_email(self):
        self.create_user()

        response = self.client.post(
            f'{BASE_URL}register/',
            self.registration_data(),
            format='json',
        )

        assert response.status_code == 400

    def test_register_does_not_allow_doctor_role(self):
        response = self.client.post(
            f'{BASE_URL}register/',
            self.registration_data(role='doctor'),
            format='json',
        )

        assert response.status_code == 201
        user = User.objects.get(email='patient@example.com')
        assert user.role == User.Role.PATIENT

    def test_login_creates_session(self):
        self.create_user()

        response = self.login()

        assert response.status_code == 200
        assert response.data['email'] == 'patient@example.com'
        assert 'sessionid' in self.client.cookies

    def test_login_rejects_wrong_password(self):
        self.create_user()

        response = self.login(password='WrongPassword123!')

        assert response.status_code == 400

    def test_login_rejects_inactive_user(self):
        self.create_user(is_active=False)

        response = self.login()

        assert response.status_code == 400

    def test_me_requires_authentication(self):
        response = self.client.get(f'{BASE_URL}me/')

        assert response.status_code in (401, 403)

    def test_me_returns_current_user(self):
        self.create_user()
        self.login()

        response = self.client.get(f'{BASE_URL}me/')

        assert response.status_code == 200
        assert response.data['email'] == 'patient@example.com'

    def test_profile_can_be_updated(self):
        self.create_user()
        self.login()

        response = self.client.patch(
            f'{BASE_URL}me/',
            {
                'first_name': 'Мария',
                'middle_name': 'Петровна',
                'birth_date': '1995-08-21',
                'phone': '+79991234567',
            },
            format='json',
        )

        assert response.status_code == 200
        assert response.data['first_name'] == 'Мария'
        assert response.data['middle_name'] == 'Петровна'
        assert response.data['birth_date'] == '1995-08-21'

        self.client.logout()
        user = User.objects.get(email='patient@example.com')
        assert user.phone == '+79991234567'

    def test_profile_cannot_change_role(self):
        self.create_user()
        self.login()

        response = self.client.patch(
            f'{BASE_URL}me/',
            {'role': 'doctor'},
            format='json',
        )

        assert response.status_code == 200
        assert response.data['role'] == User.Role.PATIENT

    def test_logout_invalidates_session(self):
        self.create_user()
        self.login()

        response = self.client.post(f'{BASE_URL}logout/')

        assert response.status_code == 204

        response = self.client.get(f'{BASE_URL}me/')
        assert response.status_code in (401, 403)


@pytest.mark.django_db
class TestAccountsCSRF:
    def setup_method(self):
        self.client = APIClient(enforce_csrf_checks=True)

    def get_csrf_token(self):
        response = self.client.get(f'{BASE_URL}csrf/')

        assert response.status_code == 200
        return self.client.cookies['csrftoken'].value

    def test_registration_requires_csrf(self):
        response = self.client.post(
            f'{BASE_URL}register/',
            {
                'email': 'patient@example.com',
                'first_name': 'Анна',
                'last_name': 'Иванова',
                'password': PASSWORD,
                'password_confirm': PASSWORD,
            },
            format='json',
        )

        assert response.status_code == 403

    def test_registration_accepts_valid_csrf(self):
        token = self.get_csrf_token()

        response = self.client.post(
            f'{BASE_URL}register/',
            {
                'email': 'patient@example.com',
                'first_name': 'Анна',
                'last_name': 'Иванова',
                'password': PASSWORD,
                'password_confirm': PASSWORD,
            },
            format='json',
            HTTP_X_CSRFTOKEN=token,
        )

        assert response.status_code == 201

    def test_login_requires_csrf(self):
        User.objects.create_user(
            email='patient@example.com',
            password=PASSWORD,
            first_name='Анна',
            last_name='Иванова',
        )

        response = self.client.post(
            f'{BASE_URL}login/',
            {'email': 'patient@example.com', 'password': PASSWORD},
            format='json',
        )

        assert response.status_code == 403

    def test_login_accepts_valid_csrf(self):
        User.objects.create_user(
            email='patient@example.com',
            password=PASSWORD,
            first_name='Анна',
            last_name='Иванова',
        )
        token = self.get_csrf_token()

        response = self.client.post(
            f'{BASE_URL}login/',
            {'email': 'patient@example.com', 'password': PASSWORD},
            format='json',
            HTTP_X_CSRFTOKEN=token,
        )

        assert response.status_code == 200
