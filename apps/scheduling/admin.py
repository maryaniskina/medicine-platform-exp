from django.contrib import admin

from apps.scheduling.models import WeeklySchedule


@admin.register(WeeklySchedule)
class WeeklyScheduleAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'doctor_clinic',
        'weekday',
        'start_time',
        'end_time',
        'valid_from',
        'valid_until',
    )
    list_display_links = ('id', 'doctor_clinic')
    list_filter = ('weekday', 'valid_from', 'valid_until')
    search_fields = (
        'doctor_clinic__doctor__first_name',
        'doctor_clinic__doctor__last_name',
        'doctor_clinic__clinic__name',
    )
    autocomplete_fields = ('doctor_clinic',)
    ordering = ('weekday', 'start_time')
    list_per_page = 25
