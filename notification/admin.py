from django.contrib import admin
from unfold.admin import ModelAdmin

from notification.models import Notification


@admin.register(Notification)
class NotificationAdmin(ModelAdmin):
    list_display = (
        "user",
        "title",
        "notification_type",
        "is_read",
        "created_at",
    )
    list_filter = ("notification_type", "is_read", "created_at")
    search_fields = ("title", "message", "user__username")
    raw_id_fields = ("user",)
    readonly_fields = ("created_at",)
