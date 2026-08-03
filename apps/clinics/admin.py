from django.contrib import admin

from apps.clinics.models import Clinic


@admin.register(Clinic)
class ClinicAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'name',
        'external_id',
        'address',
        'phone',
        'email',
        'is_active',
        'created_at',
    )
    list_display_links = ('id', 'name')
    list_filter = ('is_active', 'created_at')
    search_fields = (
        'name',
        'external_id',
        'address',
        'phone',
        'email',
    )
    ordering = ('name',)
    readonly_fields = (
        'external_id',
        'created_at',
        'updated_at',
    )
    list_per_page = 25
    date_hierarchy = 'created_at'
    fieldsets = (
        (
            'Основная информация',
            {
                'fields': (
                    'name',
                    'address',
                    'phone',
                    'email',
                    'is_active',
                ),
            },
        ),
        (
            'Координаты',
            {
                'fields': ('latitude', 'longitude'),
            },
        ),
        (
            'Интеграция',
            {
                'fields': (
                    'external_id',
                    'created_at',
                    'updated_at',
                ),
            },
        ),
    )
