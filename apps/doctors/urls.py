from django.urls import path

from apps.doctors.views import (
    DoctorDetailView,
    DoctorListView,
    SpecializationListView,
)

app_name = 'doctors'

urlpatterns = [
    path('', DoctorListView.as_view(), name='list'),
    path(
        'specializations/',
        SpecializationListView.as_view(),
        name='specializations',
    ),
    path('<int:pk>/', DoctorDetailView.as_view(), name='detail'),
]
