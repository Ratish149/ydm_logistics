from rest_framework import serializers

from notification.models import Notification


class NotificationSerializer(serializers.ModelSerializer):
    created_by = serializers.SerializerMethodField()

    class Meta:
        model = Notification
        fields = [
            "id",
            "user",
            "created_by",
            "title",
            "message",
            "notification_type",
            "is_read",
            "data",
            "created_at",
        ]
        read_only_fields = [
            "id",
            "created_by",
            "title",
            "message",
            "notification_type",
            "data",
            "created_at",
        ]

    def get_created_by(self, obj):
        if obj.user:
            return obj.user.get_full_name() or obj.user.username
        return "Anonymous"
