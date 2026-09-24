from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import extend_schema
from rest_framework import generics, status
from rest_framework.exceptions import NotFound, ValidationError
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.notifications.models import Notification
from apps.notifications.serializers import NotificationSerializer
from apps.notifications.services import (
    mark_all_notifications_as_read,
    mark_notification_as_read,
)


class NotificationListView(generics.ListAPIView):
    serializer_class = NotificationSerializer

    def get_queryset(self):
        queryset = Notification.objects.filter(
            recipient=self.request.user,
        ).select_related('appointment')
        unread = self.request.query_params.get('unread')
        if unread is not None:
            if unread.lower() not in {'true', 'false'}:
                raise ValidationError(
                    {
                        'unread': 'Используй true или false.',
                    }
                )
            queryset = queryset.filter(
                read_at__isnull=unread.lower() == 'true',
            )
        return queryset

    @extend_schema(
        summary='Список уведомлений',
        description=('Возвращает уведомления только текущего пользователя.'),
        responses={200: NotificationSerializer(many=True)},
        tags=['Notifications'],
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)


class UnreadNotificationCountView(APIView):
    @extend_schema(
        summary=('Количество непрочитанных уведомлений'),
        responses={200: OpenApiTypes.OBJECT},
        tags=['Notifications'],
    )
    def get(self, request):
        count = Notification.objects.filter(
            recipient=request.user,
            read_at__isnull=True,
        ).count()
        return Response({'unread_count': count})


class NotificationReadView(APIView):
    @extend_schema(
        summary='Отметить уведомление прочитанным',
        responses={200: NotificationSerializer},
        tags=['Notifications'],
    )
    def patch(self, request, notification_id):
        try:
            notification = Notification.objects.get(
                pk=notification_id,
                recipient=request.user,
            )
        except Notification.DoesNotExist as err:
            raise NotFound('Уведомление не найдено.') from err

        if notification.read_at is None:
            notification = mark_notification_as_read(notification=notification)
        return Response(NotificationSerializer(notification).data)


class MarkAllNotificationsReadView(APIView):
    @extend_schema(
        summary=('Отметить все уведомления прочитанными'),
        responses={200: OpenApiTypes.OBJECT},
        tags=['Notifications'],
    )
    def post(self, request):
        updated_count = mark_all_notifications_as_read(recipient=request.user)
        return Response({'updated_count': updated_count}, status=status.HTTP_200_OK)
