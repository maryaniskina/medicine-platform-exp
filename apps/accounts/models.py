from django.contrib.auth.models import AbstractUser
from django.db import models

from apps.accounts.managers import UserManager


class User(AbstractUser):
    class Role(models.TextChoices):
        PATIENT = 'patient', 'Пациент'
        DOCTOR = 'doctor', 'Доктор'

    username = None

    email = models.EmailField(unique=True, db_index=False)
    phone = models.CharField('Телефон', max_length=20, blank=True, default='')
    first_name = models.CharField('Имя', max_length=150)
    last_name = models.CharField('Фамилия', max_length=150)
    middle_name = models.CharField('Отчество', max_length=150, blank=True, default='')
    birth_date = models.DateField('Дата рождения', null=True, blank=True)

    role = models.CharField(
        'Роль', max_length=20, choices=Role.choices, default=Role.PATIENT
    )

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['first_name', 'last_name']

    objects = UserManager()

    class Meta:
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'
        ordering = ('email',)

    def __str__(self) -> str:
        return f'[{self.pk}, {self.email}] - {self.full_name}'

    @property
    def full_name(self):
        return f'{self.first_name} {self.last_name}'
