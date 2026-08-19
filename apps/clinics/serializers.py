from rest_framework import serializers

from apps.clinics.models import Clinic


class ClinicSerializer(serializers.ModelSerializer):
    class Meta:
        model = Clinic
        fields = [
            'id',
            'name',
            'address',
            'latitude',
            'longitude',
            'phone',
            'email',
        ]
        read_only_fields = fields
