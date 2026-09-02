import pytest


@pytest.mark.django_db
class TestUserModel:
    def test_create_user(self, user_factory, password):
        user = user_factory()

        assert user.email == 'patient@example.com'
        assert user.check_password(password)
        assert user.is_active is True

    def test_email_is_normalized(self, user_factory):
        user = user_factory(email='Patient@Example.COM')

        assert user.email == 'Patient@example.com'

    def test_user_str(self, user_factory):
        user = user_factory(
            first_name='Анна',
            last_name='Иванова',
        )

        assert str(user) == user.email
