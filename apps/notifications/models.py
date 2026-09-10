from django.conf import settings
from django.db import models


class Notification(models.Model):
    class Type(models.TextChoices):
        APPOINTMENT_BOOKED = 'appointment_booked', 'Новая запись'
        APPOINTMENT_CANCELLED = 'appointment_cancelled', 'Отмена записи'
        APPOINTMENT_REMINDER = 'appointment_reminder', 'Напоминание о приёме'

    recipient = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='notifications',
        verbose_name='Получатель',
    )
    appointment = models.ForeignKey(
        'appointments.Appointment',
        on_delete=models.CASCADE,
        related_name='notifications',
        verbose_name='Запись на приём',
    )
    notification_type = models.CharField(
        max_length=32,
        choices=Type.choices,
        verbose_name='Тип уведомления',
    )
    title = models.CharField(max_length=150, verbose_name='Заголовок')
    message = models.TextField(verbose_name='Текст')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Создано')
    read_at = models.DateTimeField(
        null=True,
        blank=True,
        db_index=True,
        verbose_name='Прочитано',
    )

    class Meta:
        ordering = ['-created_at', '-pk']
        verbose_name = 'Уведомление'
        verbose_name_plural = 'Уведомления'
        constraints = [
            models.UniqueConstraint(
                fields=['recipient', 'appointment', 'notification_type'],
                name='unique_appointment_notif',
            ),
        ]
        indexes = [
            models.Index(
                fields=['recipient', 'read_at', '-created_at'],
                name='notif_recipient_read_idx',
            ),
        ]

    @property
    def is_read(self):
        return self.read_at is not None

    def __str__(self) -> 'str':
        return f'{self.title} — {self.recipient}'
