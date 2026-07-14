from django.contrib.auth.models import UserManager as BaseUserManager


class UserManager(BaseUserManager):
    use_in_migrations = True

    def _create_user(self, email: str, password: str | None, **extra_fields):
        if not email:
            raise ValueError('Email must be provided.')

        email = self.normalize_email(email)

        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)

        return user

    def create_user(
        self,
        email: str,
        password: str | None = None,
        **extra_fields,
    ):
        extra_fields.setdefault('is_staff', False)
        extra_fields.setdefault('is_superuser', False)

        if extra_fields.get('is_staff'):
            raise ValueError('Regular user cannot have is_staff=True.')

        if extra_fields.get('is_superuser'):
            raise ValueError('Regular user cannot have is_superuser=True.')

        return self._create_user(email, password, **extra_fields)

    def create_superuser(
        self,
        email: str,
        password: str | None = None,
        **extra_fields,
    ):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')

        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')

        return self._create_user(email, password, **extra_fields)
