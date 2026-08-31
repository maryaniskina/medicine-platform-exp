from django.urls import path

from apps.scheduling.views import AvailableSlotsView

app_name = 'scheduling'

urlpatterns = [
    path(
        'slots/',
        AvailableSlotsView.as_view(),
        name='available-slots',
    ),
]
