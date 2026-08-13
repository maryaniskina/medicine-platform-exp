from django.conf import settings
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models


class Specialization(models.Model):
    name = models.CharField(max_length=150, unique=True)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['name']
        verbose_name = 'Специализация'
        verbose_name_plural = 'Специализации'

    def __str__(self) -> 'str':
        return self.name


class Doctor(models.Model):
    external_id = models.CharField(max_length=100, unique=True)
    first_name = models.CharField(max_length=150)
    last_name = models.CharField(max_length=150)
    middle_name = models.CharField(max_length=150, blank=True)
    email = models.EmailField(unique=True)
    photo_url = models.URLField(blank=True)
    description = models.TextField(blank=True)
    years_of_experience = models.PositiveSmallIntegerField(default=0)
    specializations = models.ManyToManyField(
        Specialization,
        related_name='doctors',
        blank=True,
    )
    clinics = models.ManyToManyField(
        'clinics.Clinic',
        through='DoctorClinic',
        related_name='doctors',
    )
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='doctor_profile',
        null=True,
        blank=True,
    )

    class Meta:
        ordering = ['last_name', 'first_name', 'middle_name']
        verbose_name = 'Врач'
        verbose_name_plural = 'Врачи'

    def __str__(self) -> 'str':
        full_name = f'{self.last_name} {self.first_name}'
        if self.middle_name:
            full_name = f'{full_name} {self.middle_name}'
        return full_name


class DoctorClinic(models.Model):
    doctor = models.ForeignKey(
        Doctor,
        on_delete=models.CASCADE,
        related_name='clinic_assignments',
    )
    clinic = models.ForeignKey(
        'clinics.Clinic',
        on_delete=models.PROTECT,
        related_name='doctor_assignments',
    )
    price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[MinValueValidator(0)],
    )
    duration_minutes = models.PositiveSmallIntegerField(
        default=30,
        validators=[
            MinValueValidator(5),
            MaxValueValidator(240),
        ],
    )
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['clinic__name', 'doctor__last_name']
        constraints = [
            models.UniqueConstraint(
                fields=['doctor', 'clinic'],
                name='unique_doctor_clinic',
            ),
            models.CheckConstraint(
                condition=models.Q(duration_minutes__gte=5),
                name='doctor_clinic_duration_min_5',
            ),
            models.CheckConstraint(
                condition=models.Q(duration_minutes__lte=240),
                name='doctor_clinic_duration_max_240',
            ),
            models.CheckConstraint(
                condition=models.Q(price__gte=0) | models.Q(price__isnull=True),
                name='doctor_clinic_price_nonnegative',
            ),
        ]
        verbose_name = 'Врач в клинике'
        verbose_name_plural = 'Врачи в клиниках'

    def __str__(self) -> 'str':
        return f'{self.doctor} — {self.clinic}'
