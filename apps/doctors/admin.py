from django.contrib import admin

from apps.doctors.models import Doctor, DoctorClinic, Specialization


@admin.register(Specialization)
class SpecializationAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'is_active', 'created_at')
    list_display_links = ('id', 'name')
    list_filter = ('is_active',)
    search_fields = ('name', 'description')
    ordering = ('name',)
    readonly_fields = ('created_at', 'updated_at')


class DoctorClinicInline(admin.TabularInline):
    model = DoctorClinic
    extra = 1
    autocomplete_fields = ('clinic',)
    fields = ('clinic', 'price', 'duration_minutes', 'is_active')


@admin.register(Doctor)
class DoctorAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'last_name',
        'first_name',
        'middle_name',
        'years_of_experience',
        'is_active',
        'created_at',
    )
    list_display_links = ('id', 'last_name', 'first_name')
    list_filter = ('is_active', 'specializations')
    search_fields = (
        'first_name',
        'last_name',
        'middle_name',
        'external_id',
    )
    ordering = ('last_name', 'first_name', 'middle_name')
    filter_horizontal = ('specializations',)
    readonly_fields = ('created_at', 'updated_at')
    inlines = (DoctorClinicInline,)
    list_per_page = 25
    save_on_top = True
    fieldsets = (
        (
            'Основная информация',
            {
                'fields': (
                    'external_id',
                    ('last_name', 'first_name', 'middle_name'),
                    'photo_url',
                    'description',
                ),
            },
        ),
        (
            'Профессиональная информация',
            {
                'fields': (
                    'years_of_experience',
                    'specializations',
                    'is_active',
                ),
            },
        ),
        (
            'Системная информация',
            {
                'fields': ('created_at', 'updated_at'),
                'classes': ('collapse',),
            },
        ),
    )


@admin.register(DoctorClinic)
class DoctorClinicAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'doctor',
        'clinic',
        'price',
        'duration_minutes',
        'is_active',
    )
    list_display_links = ('id', 'doctor')
    list_filter = ('is_active', 'clinic')
    search_fields = (
        'doctor__first_name',
        'doctor__last_name',
        'clinic__name',
        'clinic__address',
    )
    autocomplete_fields = ('doctor', 'clinic')
    readonly_fields = ('created_at', 'updated_at')
    list_per_page = 25
