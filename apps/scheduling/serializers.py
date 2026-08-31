from datetime import date as date_type
from datetime import datetime

from rest_framework import serializers


class SlotQuerySerializer(serializers.Serializer):
    doctor_clinic_id = serializers.IntegerField(min_value=1)
    date = serializers.DateField()

    def validate_date(self, value: date_type) -> date_type:
        if isinstance(value, datetime):
            raise serializers.ValidationError(
                'Укажи дату без времени.',
            )

        return value


class SlotSerializer(serializers.Serializer):
    start = serializers.DateTimeField()
    end = serializers.DateTimeField()


class AvailableSlotsResponseSerializer(serializers.Serializer):
    doctor_clinic_id = serializers.IntegerField()
    date = serializers.DateField()
    slots = SlotSerializer(many=True)
