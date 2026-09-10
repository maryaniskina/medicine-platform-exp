from django.urls import path

from apps.notifications.views import (
    MarkAllNotificationsReadView,
    NotificationListView,
    NotificationReadView,
    UnreadNotificationCountView,
)

app_name = 'notifications'

urlpatterns = [
    path('', NotificationListView.as_view(), name='notification-list'),
    path('unread-count/', UnreadNotificationCountView.as_view(), name='unread-count'),
    path('read-all/', MarkAllNotificationsReadView.as_view(), name='read-all'),
    path('<int:notification_id>/read/', NotificationReadView.as_view(), name='read'),
]
