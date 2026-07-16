import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIRequestFactory

from apps.accounts.serializers import (
    LoginSerializer,
    ProfileUpdateSerializer,
    RegistrationSerializer,
    UserSerializer,
)

User = get_user_model()


@pytest.mark.django_db
class TestRegistrationSerializer:
    def get_data(self, **overrides):
        data = {
            'email': 'patient@example.com',
            'phone': '+79991234567',
            'first_name': 'Анна',
            'last_name': 'Иванова',
            'password': 'StrongPassword123!',
            'password_confirm': 'StrongPassword123!',
        }
        data.update(overrides)
        return data

    def test_valid_registration(self):
        serializer = RegistrationSerializer(data=self.get_data())

        assert serializer.is_valid(), serializer.errors

    def test_create_user_hashes_password(self):
        serializer = RegistrationSerializer(data=self.get_data())

        assert serializer.is_valid(), serializer.errors
        user = serializer.save()

        assert user.check_password('StrongPassword123!')
        assert user.phone == '+79991234567'
        assert user.role == User.Role.PATIENT

    def test_passwords_must_match(self):
        serializer = RegistrationSerializer(
            data=self.get_data(password_confirm='DifferentPassword123!')
        )

        assert not serializer.is_valid()
        assert 'password_confirm' in serializer.errors

    def test_duplicate_email_is_rejected(self):
        User.objects.create_user(
            email='patient@example.com',
            password='StrongPassword123!',
            first_name='Анна',
            last_name='Иванова',
        )

        serializer = RegistrationSerializer(data=self.get_data())

        assert not serializer.is_valid()
        assert 'email' in serializer.errors

    def test_email_is_normalized(self):
        serializer = RegistrationSerializer(
            data=self.get_data(email='Patient@EXAMPLE.COM')
        )

        assert serializer.is_valid(), serializer.errors
        assert serializer.validated_data['email'] == 'patient@example.com'

    def test_role_cannot_be_set_during_registration(self):
        serializer = RegistrationSerializer(data=self.get_data(role='doctor'))

        assert serializer.is_valid(), serializer.errors
        user = serializer.save()

        assert user.role == User.Role.PATIENT

    def test_password_is_not_returned(self):
        serializer = RegistrationSerializer(data=self.get_data())

        assert serializer.is_valid(), serializer.errors
        user = serializer.save()
        response_data = UserSerializer(user).data

        assert 'password' not in response_data
        assert 'password_confirm' not in response_data


@pytest.mark.django_db
class TestLoginSerializer:
    def setup_method(self):
        self.factory = APIRequestFactory()
        self.user = User.objects.create_user(
            email='login@example.com',
            password='StrongPass123!',
            first_name='Иван',
            last_name='Иванов',
        )
        self.request = self.factory.post('/api/accounts/login/')

    def test_valid_credentials(self):
        serializer = LoginSerializer(
            data={
                'email': 'login@example.com',
                'password': 'StrongPass123!',
            },
            context={'request': self.request},
        )

        assert serializer.is_valid(), serializer.errors
        assert serializer.validated_data['user'] == self.user

    def test_invalid_password(self):
        serializer = LoginSerializer(
            data={
                'email': 'patient@example.com',
                'password': 'WrongPassword123!',
            },
            context={'request': self.request},
        )

        assert not serializer.is_valid()
        assert 'detail' in serializer.errors

    def test_inactive_user_cannot_login(self):
        self.user.is_active = False
        self.user.save(update_fields=['is_active'])

        serializer = LoginSerializer(
            data={
                'email': 'patient@example.com',
                'password': 'StrongPassword123!',
            },
            context={'request': self.request},
        )

        assert not serializer.is_valid()


@pytest.mark.django_db
class TestProfileUpdateSerializer:
    def test_update_personal_data(self):
        user = User.objects.create_user(
            email='patient@example.com',
            password='StrongPassword123!',
            first_name='Анна',
            last_name='Иванова',
        )
        serializer = ProfileUpdateSerializer(
            user,
            data={
                'first_name': 'Мария',
                'middle_name': 'Петровна',
                'birth_date': '1995-08-21',
                'phone': '+79991234567',
            },
            partial=True,
        )

        assert serializer.is_valid(), serializer.errors
        updated_user = serializer.save()

        assert updated_user.first_name == 'Мария'
        assert updated_user.middle_name == 'Петровна'
        assert updated_user.birth_date.isoformat() == '1995-08-21'
        assert updated_user.phone == '+79991234567'

    def test_role_is_not_editable(self):
        user = User.objects.create_user(
            email='patient@example.com',
            password='StrongPassword123!',
            first_name='Анна',
            last_name='Иванова',
        )
        serializer = ProfileUpdateSerializer(
            user,
            data={'role': 'doctor'},
            partial=True,
        )

        assert serializer.is_valid(), serializer.errors
        updated_user = serializer.save()

        assert updated_user.role == User.Role.PATIENT
