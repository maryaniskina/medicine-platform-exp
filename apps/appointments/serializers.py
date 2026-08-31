from django.contrib.auth import get_user_model
from rest_framework import serializers

from apps.appointments.models import Appointment
from apps.doctors.models import DoctorClinic


class AppointmentPatientSerializer(serializers.ModelSerializer):
    full_name = serializers.CharField(read_only=True)

    class Meta:
        model = get_user_model()
        fields = [
            'id',
            'full_name',
            'phone',
            'birth_date',
        ]


class DoctorAppointmentSerializer(serializers.ModelSerializer):
    patient = AppointmentPatientSerializer(read_only=True)
    clinic_name = serializers.CharField(
        source='doctor_clinic.clinic.name',
        read_only=True,
    )

    class Meta:
        model = Appointment
        fields = [
            'id',
            'patient',
            'clinic_name',
            'start_at',
            'end_at',
            'status',
            'patient_comment',
            'cancellation_reason',
            'created_at',
        ]
        read_only_fields = fields


class AppointmentCreateSerializer(serializers.Serializer):
    doctor_clinic_id = serializers.PrimaryKeyRelatedField(
        queryset=DoctorClinic.objects.filter(
            is_active=True,
            doctor__is_active=True,
            clinic__is_active=True,
        ),
        source='doctor_clinic',
    )
    start_at = serializers.DateTimeField()
    patient_comment = serializers.CharField(
        required=False,
        allow_blank=True,
        default='',
    )


class AppointmentCancelSerializer(serializers.Serializer):
    reason = serializers.CharField(
        required=False,
        allow_blank=True,
        default='',
        max_length=1000,
    )


class PatientAppointmentSerializer(serializers.ModelSerializer):
    doctor_name = serializers.SerializerMethodField()
    clinic_name = serializers.CharField(
        source='doctor_clinic.clinic.name',
        read_only=True,
    )

    class Meta:
        model = Appointment
        fields = [
            'id',
            'doctor_name',
            'clinic_name',
            'start_at',
            'end_at',
            'status',
            'patient_comment',
            'cancellation_reason',
            'cancelled_at',
            'created_at',
        ]
        read_only_fields = fields

    def get_doctor_name(self, obj):
        return str(obj.doctor_clinic.doctor)
