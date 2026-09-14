from django.utils import timezone

from apps.appointments.models import Appointment
from apps.notifications.models import Notification


def create_notification(*, recipient, appointment, notification_type, title, message):
    if recipient is None:
        return None

    notification, _ = Notification.objects.get_or_create(
        recipient=recipient,
        appointment=appointment,
        notification_type=notification_type,
        defaults={
            'title': title,
            'message': message,
        },
    )
    return notification


def notify_appointment_booked(appointment):
    doctor_user = appointment.doctor_clinic.doctor.user
    start_at = timezone.localtime(appointment.start_at).strftime('%d.%m.%Y в %H:%M')
    doctor_name = str(appointment.doctor_clinic.doctor)
    clinic_name = appointment.doctor_clinic.clinic.name

    create_notification(
        recipient=appointment.patient,
        appointment=appointment,
        notification_type=Notification.Type.APPOINTMENT_BOOKED,
        title='Вы записаны на приём',
        message=f'Приём у врача {doctor_name} в клинике {clinic_name} '
        f'назначен на {start_at}.',
    )

    if doctor_user is not None:
        create_notification(
            recipient=doctor_user,
            appointment=appointment,
            notification_type=Notification.Type.APPOINTMENT_BOOKED,
            title='Новая запись на приём',
            message=f'Пациент {appointment.patient.full_name} записан '
            f'на {start_at}.',
        )


def notify_appointment_cancelled(appointment):
    doctor_user = appointment.doctor_clinic.doctor.user
    start_at = timezone.localtime(appointment.start_at).strftime('%d.%m.%Y в %H:%M')
    doctor_name = str(appointment.doctor_clinic.doctor)
    clinic_name = appointment.doctor_clinic.clinic.name

    create_notification(
        recipient=appointment.patient,
        appointment=appointment,
        notification_type=Notification.Type.APPOINTMENT_CANCELLED,
        title='Запись отменена',
        message=f'Ваш приём у врача {doctor_name} в клинике {clinic_name} '
        f'на {start_at} отменён.',
    )

    if doctor_user is not None:
        create_notification(
            recipient=doctor_user,
            appointment=appointment,
            notification_type=Notification.Type.APPOINTMENT_CANCELLED,
            title='Отмена записи',
            message=f'Пациент {appointment.patient.full_name} отменил '
            f'приём на {start_at}.',
        )


def create_appointment_reminders(appointments):
    created_count = 0

    for appointment in appointments:
        if appointment.status not in {
            Appointment.Status.BOOKED,
            Appointment.Status.CONFIRMED,
        }:
            continue

        start_at = timezone.localtime(appointment.start_at).strftime(
            '%d.%m.%Y в %H:%M'
        )
        doctor_name = str(appointment.doctor_clinic.doctor)
        clinic_name = appointment.doctor_clinic.clinic.name
        recipients = [appointment.patient]
        doctor_user = appointment.doctor_clinic.doctor.user
        if doctor_user is not None:
            recipients.append(doctor_user)

        for recipient in recipients:
            _, created = Notification.objects.get_or_create(
                recipient=recipient,
                appointment=appointment,
                notification_type=Notification.Type.APPOINTMENT_REMINDER,
                defaults={
                    'title': 'Напоминание о приёме',
                    'message': f'Завтра у вас приём у врача {doctor_name} '
                    f'в клинике {clinic_name}, {start_at}.',
                },
            )
            if created:
                created_count += 1

    return created_count


def mark_notification_as_read(*, notification):
    if notification.read_at is None:
        notification.read_at = timezone.now()
        notification.save(update_fields=['read_at'])
    return notification


def mark_all_notifications_as_read(*, recipient):
    return Notification.objects.filter(
        recipient=recipient,
        read_at__isnull=True,
    ).update(read_at=timezone.now())
