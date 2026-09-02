import pytest
from django.test import RequestFactory

from apps.accounts.serializers import (
    LoginSerializer,
    RegistrationSerializer,
)


@pytest.mark.django_db
class TestRegistrationSerializer:
    def test_valid_data(self, registration_data):
        serializer = RegistrationSerializer(data=registration_data)

        assert serializer.is_valid(), serializer.errors

    def test_password_mismatch(self, registration_data):
        registration_data['password_confirm'] = 'AnotherPassword123!'
        serializer = RegistrationSerializer(data=registration_data)

        assert not serializer.is_valid()
        assert 'password_confirm' in serializer.errors

    def test_create_user(self, registration_data, user_model):
        serializer = RegistrationSerializer(data=registration_data)
        assert serializer.is_valid(), serializer.errors

        user = serializer.save()

        assert user_model.objects.filter(pk=user.pk).exists()
        assert user.email == registration_data['email']
        assert user.check_password(registration_data['password'])


@pytest.mark.django_db
class TestLoginSerializer:
    def test_valid_credentials(self, user_factory, password):
        user = user_factory()
        request = RequestFactory().post('/api/accounts/login/')
        serializer = LoginSerializer(
            data={'email': user.email, 'password': password},
            context={'request': request},
        )

        assert serializer.is_valid(), serializer.errors

    def test_invalid_password(self, user_factory):
        user = user_factory()
        request = RequestFactory().post('/api/accounts/login/')
        serializer = LoginSerializer(
            data={
                'email': user.email,
                'password': 'WrongPassword123!',
            },
            context={'request': request},
        )

        assert not serializer.is_valid()

    def test_nonexistent_user(self, password):
        request = RequestFactory().post('/api/accounts/login/')
        serializer = LoginSerializer(
            data={
                'email': 'missing@example.com',
                'password': password,
            },
            context={'request': request},
        )

        assert not serializer.is_valid()
