from django.urls import path

from apps.clinics.views import ClinicDetailView, ClinicListView

app_name = 'clinics'

urlpatterns = [
    path('', ClinicListView.as_view(), name='list'),
    path('<int:pk>/', ClinicDetailView.as_view(), name='detail'),
]
