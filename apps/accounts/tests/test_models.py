import pytest
from django.contrib.auth import get_user_model

User = get_user_model()


@pytest.mark.django_db
class TestUserManager:
    def test_create_user_hashes_password(self):
        user = User.objects.create_user(
            email='patient@example.com',
            password='StrongPassword123!',
            first_name='Анна',
            last_name='Иванова',
        )

        assert user.password != 'StrongPassword123!'
        assert user.check_password('StrongPassword123!')

    def test_create_user_normalizes_email_domain(self):
        user = User.objects.create_user(
            email='patient@EXAMPLE.COM',
            password='StrongPassword123!',
            first_name='Анна',
            last_name='Иванова',
        )

        assert user.email == 'patient@example.com'

    def test_create_user_defaults_to_patient(self):
        user = User.objects.create_user(
            email='patient@example.com',
            password='StrongPassword123!',
            first_name='Анна',
            last_name='Иванова',
        )

        assert user.role == User.Role.PATIENT
        assert not user.is_staff
        assert not user.is_superuser

    def test_create_user_requires_email(self):
        with pytest.raises(ValueError, match='Email must be provided'):
            User.objects.create_user(
                email='',
                password='StrongPassword123!',
                first_name='Анна',
                last_name='Иванова',
            )

    def test_create_user_rejects_staff(self):
        with pytest.raises(ValueError, match='is_staff=True'):
            User.objects.create_user(
                email='patient@example.com',
                password='StrongPassword123!',
                first_name='Анна',
                last_name='Иванова',
                is_staff=True,
            )

    def test_create_user_rejects_superuser(self):
        with pytest.raises(ValueError, match='is_superuser=True'):
            User.objects.create_user(
                email='patient@example.com',
                password='StrongPassword123!',
                first_name='Анна',
                last_name='Иванова',
                is_superuser=True,
            )

    def test_create_superuser(self):
        user = User.objects.create_superuser(
            email='admin@example.com',
            password='StrongPassword123!',
            first_name='Администратор',
            last_name='MedBook',
        )

        assert user.is_staff
        assert user.is_superuser
        assert user.is_active
        assert user.check_password('StrongPassword123!')

    def test_create_superuser_rejects_invalid_flags(self):
        with pytest.raises(ValueError, match='is_staff=True'):
            User.objects.create_superuser(
                email='admin@example.com',
                password='StrongPassword123!',
                first_name='Администратор',
                last_name='MedBook',
                is_staff=False,
            )


@pytest.mark.django_db
class TestUserModel:
    def test_user_personal_data(self):
        user = User.objects.create_user(
            email='patient@example.com',
            password='StrongPassword123!',
            first_name='Иван',
            last_name='Иванов',
            middle_name='Иванович',
            birth_date='1995-08-21',
            phone='+79991234567',
        )

        user.refresh_from_db()

        assert user.first_name == 'Иван'
        assert user.last_name == 'Иванов'
        assert user.middle_name == 'Иванович'
        assert user.birth_date.isoformat() == '1995-08-21'
        assert user.phone == '+79991234567'

    def test_full_name(self):
        user = User(
            email='patient@example.com',
            first_name='Иван',
            last_name='Иванов',
        )

        assert user.full_name == 'Иван Иванов'
        assert str(user) == f'[{user.pk}, {user.email}] - Иван Иванов'

    def test_optional_personal_data(self):
        user = User.objects.create_user(
            email='patient@example.com',
            password='StrongPassword123!',
            first_name='Иван',
            last_name='Иванов',
        )

        assert user.phone == ''
        assert user.middle_name == ''
        assert user.birth_date is None
