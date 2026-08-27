from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import F, Q


class WeeklySchedule(models.Model):
    WEEKDAYS = [
        (0, 'Понедельник'),
        (1, 'Вторник'),
        (2, 'Среда'),
        (3, 'Четверг'),
        (4, 'Пятница'),
        (5, 'Суббота'),
        (6, 'Воскресенье'),
    ]

    doctor_clinic = models.ForeignKey(
        'doctors.DoctorClinic',
        on_delete=models.CASCADE,
        related_name='schedules',
        verbose_name='Врач в клинике',
    )
    weekday = models.PositiveSmallIntegerField(
        choices=WEEKDAYS,
        verbose_name='День недели',
    )
    start_time = models.TimeField(verbose_name='Начало приёма')
    end_time = models.TimeField(verbose_name='Окончание приёма')
    valid_from = models.DateField(verbose_name='Действует с')
    valid_until = models.DateField(
        null=True,
        blank=True,
        verbose_name='Действует по',
    )

    class Meta:
        ordering = ['weekday', 'start_time']
        verbose_name = 'Расписание врача'
        verbose_name_plural = 'Расписания врачей'
        constraints = [
            models.CheckConstraint(
                condition=Q(start_time__lt=F('end_time')),
                name='schedule_start_before_end',
            ),
            models.CheckConstraint(
                condition=Q(valid_until__isnull=True)
                | Q(valid_until__gte=F('valid_from')),
                name='schedule_valid_dates',
            ),
            models.UniqueConstraint(
                fields=[
                    'doctor_clinic',
                    'weekday',
                    'start_time',
                    'valid_from',
                ],
                name='unique_schedule_start',
            ),
        ]

    def clean(self):
        super().clean()

        if (
            self.doctor_clinic_id is not None
            and self.weekday is not None
            and self.start_time is not None
            and self.end_time is not None
            and self.valid_from is not None
            and self.start_time < self.end_time
        ):
            overlapping = WeeklySchedule.objects.filter(
                doctor_clinic_id=self.doctor_clinic_id,
                weekday=self.weekday,
                start_time__lt=self.end_time,
                end_time__gt=self.start_time,
            ).filter(
                Q(valid_until__isnull=True)
                | Q(valid_until__gte=self.valid_from),
            )

            if self.valid_until is not None:
                overlapping = overlapping.filter(
                    valid_from__lte=self.valid_until,
                )

            if self.pk is not None:
                overlapping = overlapping.exclude(pk=self.pk)

            if overlapping.exists():
                raise ValidationError({
                    'start_time': (
                        'Время пересекается с другим расписанием '
                        'этого врача в клинике.'
                    ),
                })

        if (
            self.valid_until is not None
            and self.valid_until < self.valid_from
        ):
            raise ValidationError({
                'valid_until': 'Дата окончания не может быть раньше даты начала.',
            })

        if self.start_time is not None and self.end_time is not None:
            if self.start_time >= self.end_time:
                raise ValidationError({
                    'end_time': 'Окончание приёма должно быть позже начала.',
                })

    def __str__(self):
        return (
            f'{self.doctor_clinic} — {self.get_weekday_display()}, '
            f'{self.start_time:%H:%M}–{self.end_time:%H:%M}'
        )
