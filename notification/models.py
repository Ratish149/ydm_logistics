from django.conf import settings
from django.db import models


class Notification(models.Model):
    NOTIFICATION_TYPE_ORDER_PLACED = "order_placed"
    NOTIFICATION_TYPE_RIDER_ASSIGNED = "rider_assigned"
    NOTIFICATION_TYPE_STATUS_UPDATED = "status_updated"

    NOTIFICATION_TYPE_CHOICES = [
        (NOTIFICATION_TYPE_ORDER_PLACED, "Order Placed"),
        (NOTIFICATION_TYPE_RIDER_ASSIGNED, "Rider Assigned"),
        (NOTIFICATION_TYPE_STATUS_UPDATED, "Status Updated"),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="notifications",
        db_index=True,
        null=True,
        blank=True,
    )
    title = models.CharField(max_length=255)
    message = models.TextField()
    notification_type = models.CharField(
        max_length=50, choices=NOTIFICATION_TYPE_CHOICES, db_index=True
    )
    is_read = models.BooleanField(default=False, db_index=True)
    data = models.JSONField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        user_str = self.user.username if self.user else "Global"
        return f"{user_str} - {self.title} - Read: {self.is_read}"
