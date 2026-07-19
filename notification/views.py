from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import status
from rest_framework.generics import ListAPIView, RetrieveUpdateDestroyAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from notification.filters import NotificationFilter
from notification.models import Notification
from notification.serializers import NotificationSerializer
from notification.services.notification_service import bulk_mark_notifications_as_read
from ydm.utils.pagination import CustomPagination


class NotificationListAPIView(ListAPIView):
    """
    GET /api/notifications/ — List all notifications for the authenticated user.
    """

    serializer_class = NotificationSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_class = NotificationFilter
    pagination_class = CustomPagination

    def get_queryset(self):
        user = self.request.user
        if user.role == "ydm":
            return Notification.objects.select_related("user").filter(
                notification_type__in=[
                    Notification.NOTIFICATION_TYPE_ORDER_PLACED,
                    Notification.NOTIFICATION_TYPE_STATUS_UPDATED,
                ]
            )
        elif user.role == "YDM_Rider":
            return Notification.objects.select_related("user").filter(
                notification_type=Notification.NOTIFICATION_TYPE_RIDER_ASSIGNED,
                user=user,
            )
        elif user.role == "vendor":
            return Notification.objects.select_related("user").filter(user=user)
        return Notification.objects.none()


class NotificationDetailAPIView(RetrieveUpdateDestroyAPIView):
    """
    GET    /api/notifications/<id>/ — Retrieve details of a specific notification.
    PATCH  /api/notifications/<id>/ — Update a notification (e.g. mark it as read).
    DELETE /api/notifications/<id>/ — Delete a notification.
    """

    serializer_class = NotificationSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if user.role == "ydm":
            return Notification.objects.select_related("user").filter(
                notification_type__in=[
                    Notification.NOTIFICATION_TYPE_ORDER_PLACED,
                    Notification.NOTIFICATION_TYPE_STATUS_UPDATED,
                ]
            )
        elif user.role == "YDM_Rider":
            return Notification.objects.select_related("user").filter(
                notification_type=Notification.NOTIFICATION_TYPE_RIDER_ASSIGNED,
                user=user,
            )
        elif user.role == "vendor":
            return Notification.objects.select_related("user").filter(user=user)
        return Notification.objects.none()


class NotificationBulkReadAPIView(APIView):
    """
    POST /api/notifications/bulk-read/ — Mark multiple or all notifications as read.
    """

    permission_classes = [IsAuthenticated]

    def post(self, request):
        mark_all = request.data.get("all", False)
        notification_ids = request.data.get("notification_ids", [])

        if not mark_all and not notification_ids:
            return Response(
                {
                    "detail": "Either 'all' must be true or 'notification_ids' must be provided."
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        updated_count = bulk_mark_notifications_as_read(
            user=request.user,
            notification_ids=notification_ids,
            mark_all=mark_all,
        )

        return Response(
            {"detail": f"Successfully marked {updated_count} notifications as read."},
            status=status.HTTP_200_OK,
        )
