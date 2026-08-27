from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import F, Q
from django.utils import timezone


class Appointment(models.Model):
    class Status(models.TextChoices):
        BOOKED = 'booked', 'Записан'
        CONFIRMED = 'confirmed', 'Подтверждён'
        COMPLETED = 'completed', 'Завершён'
        CANCELLED = 'cancelled', 'Отменён'
        NO_SHOW = 'no_show', 'Не явился'

    patient = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='appointments',
        verbose_name='Пациент',
    )
    doctor_clinic = models.ForeignKey(
        'doctors.DoctorClinic',
        on_delete=models.PROTECT,
        related_name='appointments',
        verbose_name='Врач в клинике',
    )
    start_at = models.DateTimeField(verbose_name='Начало приёма')
    end_at = models.DateTimeField(verbose_name='Окончание приёма')
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.BOOKED,
        db_index=True,
        verbose_name='Статус записи',
    )
    patient_comment = models.TextField(
        blank=True,
        verbose_name='Комментарий пациента',
    )
    cancellation_reason = models.TextField(
        blank=True,
        verbose_name='Причина отмены',
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Создана',
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name='Обновлена',
    )
    cancelled_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='Время отмены',
    )

    class Meta:
        ordering = ['start_at']
        verbose_name = 'Запись на приём'
        verbose_name_plural = 'Записи на приём'
        indexes = [
            models.Index(
                fields=['doctor_clinic', 'start_at'],
                name='appointment_doctor_start_idx',
            ),
            models.Index(
                fields=['patient', 'start_at'],
                name='appointment_patient_start_idx',
            ),
        ]
        constraints = [
            models.CheckConstraint(
                condition=Q(start_at__lt=F('end_at')),
                name='appointment_start_before_end',
            ),
            models.UniqueConstraint(
                fields=['doctor_clinic', 'start_at'],
                condition=Q(
                    status__in=['booked', 'confirmed'],
                ),
                name='unique_active_doctor_slot',
            ),
        ]

    def clean(self):
        super().clean()

        if (
            self.start_at is not None
            and self.end_at is not None
            and self.start_at >= self.end_at
        ):
            raise ValidationError({
                'end_at': 'Окончание приёма должно быть позже начала.',
            })

        if self.start_at is not None and self.start_at <= timezone.now():
            if self._state.adding:
                raise ValidationError({
                    'start_at': 'Нельзя записаться на прошедшее время.',
                })

    def save(self, *args, **kwargs):
        if self.status == self.Status.CANCELLED and self.cancelled_at is None:
            self.cancelled_at = timezone.now()

        super().save(*args, **kwargs)

    def __str__(self) -> 'str':
        return (
            f'{self.patient} — {self.doctor_clinic.doctor} — '
            f'{self.start_at:%Y-%m-%d %H:%M}'
        )
