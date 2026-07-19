from django_filters import rest_framework as filters

from notification.models import Notification


class NotificationFilter(filters.FilterSet):
    class Meta:
        model = Notification
        fields = {
            "is_read": ["exact"],
            "notification_type": ["exact"],
        }
