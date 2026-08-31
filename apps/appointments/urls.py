from django.urls import path

from apps.appointments.views import (
    AppointmentCancelView,
    AppointmentCreateView,
    DoctorAppointmentListView,
    PatientAppointmentListView,
)

app_name = 'appointments'

urlpatterns = [
    path(
        '',
        AppointmentCreateView.as_view(),
        name='appointment-create',
    ),
    path(
        'doctor/',
        DoctorAppointmentListView.as_view(),
        name='doctor-appointments',
    ),
    path(
        '<int:appointment_id>/cancel/',
        AppointmentCancelView.as_view(),
        name='appointment-cancel',
    ),
    path(
        'my/',
        PatientAppointmentListView.as_view(),
        name='my-appointments',
    ),
]
