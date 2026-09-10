import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('appointments', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Notification',
            fields=[
                (
                    'id',
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name='ID',
                    ),
                ),
                (
                    'notification_type',
                    models.CharField(
                        choices=[
                            ('appointment_booked', 'Новая запись'),
                            ('appointment_cancelled', 'Отмена записи'),
                            ('appointment_reminder', 'Напоминание о приёме'),
                        ],
                        max_length=32,
                        verbose_name='Тип уведомления',
                    ),
                ),
                ('title', models.CharField(max_length=150, verbose_name='Заголовок')),
                ('message', models.TextField(verbose_name='Текст')),
                (
                    'created_at',
                    models.DateTimeField(auto_now_add=True, verbose_name='Создано'),
                ),
                (
                    'read_at',
                    models.DateTimeField(
                        blank=True,
                        db_index=True,
                        null=True,
                        verbose_name='Прочитано',
                    ),
                ),
                (
                    'appointment',
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name='notifications',
                        to='appointments.appointment',
                        verbose_name='Запись на приём',
                    ),
                ),
                (
                    'recipient',
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name='notifications',
                        to=settings.AUTH_USER_MODEL,
                        verbose_name='Получатель',
                    ),
                ),
            ],
            options={
                'verbose_name': 'Уведомление',
                'verbose_name_plural': 'Уведомления',
                'ordering': ['-created_at', '-pk'],
            },
        ),
        migrations.AddConstraint(
            model_name='notification',
            constraint=models.UniqueConstraint(
                fields=('recipient', 'appointment', 'notification_type'),
                name='unique_appointment_notification',
            ),
        ),
        migrations.AddIndex(
            model_name='notification',
            index=models.Index(
                fields=['recipient', 'read_at', '-created_at'],
                name='notification_recipient_read_idx',
            ),
        ),
    ]
