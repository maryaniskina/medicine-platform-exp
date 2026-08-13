from rest_framework import serializers

from apps.doctors.models import Doctor, DoctorClinic, Specialization


class SpecializationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Specialization
        fields = ['id', 'name']


class DoctorClinicSerializer(serializers.ModelSerializer):
    clinic_id = serializers.IntegerField(source='clinic.id', read_only=True)
    clinic_name = serializers.CharField(
        source='clinic.name',
        read_only=True,
    )
    clinic_address = serializers.CharField(
        source='clinic.address',
        read_only=True,
    )

    class Meta:
        model = DoctorClinic
        fields = [
            'clinic_id',
            'clinic_name',
            'clinic_address',
            'price',
            'duration_minutes',
        ]


class DoctorListSerializer(serializers.ModelSerializer):
    specializations = SpecializationSerializer(many=True, read_only=True)

    class Meta:
        model = Doctor
        fields = [
            'id',
            'first_name',
            'last_name',
            'middle_name',
            'photo_url',
            'years_of_experience',
            'specializations',
        ]


class DoctorDetailSerializer(DoctorListSerializer):
    clinics = serializers.SerializerMethodField()
    description = serializers.CharField(read_only=True)

    class Meta(DoctorListSerializer.Meta):
        fields = [
            *DoctorListSerializer.Meta.fields,
            'description',
            'clinics',
        ]

    def get_clinics(self, obj):
        assignments = obj.clinic_assignments.filter(
            is_active=True,
            clinic__is_active=True,
        ).select_related('clinic')

        return DoctorClinicSerializer(assignments, many=True).data
