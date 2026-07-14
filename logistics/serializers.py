from rest_framework import serializers

from logistics.models import Order, OrderComment, OrderStatusHistory


class OrderStatusHistorySerializer(serializers.ModelSerializer):
    changed_by_name = serializers.CharField(
        source="changed_by.get_full_name", default="", read_only=True
    )

    class Meta:
        model = OrderStatusHistory
        fields = ["status", "changed_by", "changed_by_name", "created_at"]


class OrderCommentSerializer(serializers.ModelSerializer):
    commented_by_name = serializers.CharField(
        source="commented_by.get_full_name", default="", read_only=True
    )

    class Meta:
        model = OrderComment
        fields = [
            "id",
            "commented_by",
            "commented_by_name",
            "comment_type",
            "message",
            "created_at",
        ]
        read_only_fields = ["id", "commented_by", "created_at"]


class OrderDetailSerializer(serializers.ModelSerializer):
    status_history = OrderStatusHistorySerializer(many=True, read_only=True)
    comments = OrderCommentSerializer(many=True, read_only=True)
    project_client = serializers.CharField(
        source="user.first_name", default="", read_only=True
    )
    assigned_rider_name = serializers.CharField(
        source="assigned_rider.get_full_name", default="", read_only=True
    )

    class Meta:
        model = Order
        fields = [
            "tracking_number",
            "external_order_code",
            "project_client",
            "sender_name",
            "sender_phone",
            "sender_address",
            "sender_email",
            "recipient_name",
            "recipient_phone",
            "recipient_email",
            "recipient_address",
            "recipient_city",
            "recipient_district",
            "cod_amount",
            "delivery_charge",
            "payment_type",
            "product",
            "special_instructions",
            "status",
            "remarks",
            "pickup_date",
            "delivered_at",
            "delivery_attempts",
            "assigned_rider",
            "assigned_rider_name",
            "created_at",
            "updated_at",
            "status_history",
            "comments",
        ]


class OrderCreateSerializer(serializers.ModelSerializer):
    assigned_rider_id = serializers.IntegerField(
        write_only=True, required=False, allow_null=True
    )

    class Meta:
        model = Order
        fields = [
            "external_order_code",
            "sender_name",
            "sender_phone",
            "sender_address",
            "sender_email",
            "recipient_name",
            "recipient_phone",
            "recipient_email",
            "recipient_address",
            "recipient_city",
            "recipient_district",
            "cod_amount",
            "delivery_charge",
            "payment_type",
            "remarks",
            "product",
            "special_instructions",
            "pickup_date",
            "delivered_at",
            "assigned_rider_id",
        ]

    def create(self, validated_data):
        request = self.context.get("request")
        user = request.user if request else self.context.get("user")
        assigned_rider_id = validated_data.pop("assigned_rider_id", None)
        if assigned_rider_id:
            from django.contrib.auth import get_user_model

            User = get_user_model()
            validated_data["assigned_rider"] = User.objects.filter(
                id=assigned_rider_id
            ).first()

        from logistics.services.order_service import create_order

        return create_order(user=user, **validated_data)


class OrderStatusUpdateSerializer(serializers.Serializer):
    status = serializers.ChoiceField(choices=Order.STATUS_CHOICES)

    def update(self, instance, validated_data):
        from logistics.services.order_service import update_order_status

        webhook_url = self.context.get("webhook_url")
        user = self.context.get("user")
        return update_order_status(
            order=instance,
            new_status=validated_data["status"],
            changed_by=user,
            webhook_url=webhook_url,
        )
