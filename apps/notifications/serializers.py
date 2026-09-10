from rest_framework import serializers

from apps.notifications.models import Notification


class NotificationSerializer(serializers.ModelSerializer):
    is_read = serializers.BooleanField(read_only=True)

    class Meta:
        model = Notification
        fields = [
            'id',
            'appointment',
            'notification_type',
            'title',
            'message',
            'created_at',
            'read_at',
            'is_read',
        ]
        read_only_fields = fields
