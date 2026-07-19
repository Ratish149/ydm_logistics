from django.urls import path

from notification.views import (
    NotificationBulkReadAPIView,
    NotificationDetailAPIView,
    NotificationListAPIView,
)

urlpatterns = [
    path("notifications/", NotificationListAPIView.as_view(), name="notification-list"),
    path(
        "notifications/<int:pk>/",
        NotificationDetailAPIView.as_view(),
        name="notification-detail",
    ),
    path(
        "notifications/bulk-read/",
        NotificationBulkReadAPIView.as_view(),
        name="notification-bulk-read",
    ),
]
