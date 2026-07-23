from django.contrib.auth import get_user_model
from rest_framework import serializers

from account.serializers import UserListSerializer
from logistics.models import Order
from logistics.serializers import OrderListSerializer
from payment.models import CodPayment

User = get_user_model()


class CodPaymentSerializer(serializers.ModelSerializer):
    orders = serializers.PrimaryKeyRelatedField(
        queryset=Order.objects.all(), many=True, required=False
    )
    orders_detail = OrderListSerializer(source="orders", many=True, read_only=True)
    user_detail = UserListSerializer(source="user", read_only=True)
    created_by_detail = UserListSerializer(source="created_by", read_only=True)

    class Meta:
        model = CodPayment
        fields = [
            "id",
            "payment_number",
            "user",
            "user_detail",
            "created_by",
            "created_by_detail",
            "orders",
            "orders_detail",
            "delivery_amount",
            "total_amount",
            "status",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["created_by", "created_at", "updated_at"]


class CodPaymentListSerializer(serializers.ModelSerializer):
    transfer_date = serializers.DateTimeField(source="created_at", read_only=True)
    order_count = serializers.SerializerMethodField()
    delivery_amount = serializers.DecimalField(
        max_digits=12, decimal_places=2, read_only=True
    )
    amount = serializers.DecimalField(
        source="total_amount", max_digits=12, decimal_places=2, read_only=True
    )

    class Meta:
        model = CodPayment
        fields = [
            "id",
            "payment_number",
            "transfer_date",
            "order_count",
            "delivery_amount",
            "amount",
            "status",
        ]

    def get_order_count(self, obj):
        return obj.orders.count()


class CodPaymentOrderListSerializer(serializers.ModelSerializer):
    cod = serializers.DecimalField(
        source="cod_amount", max_digits=10, decimal_places=2, read_only=True
    )
    delivery_charge = serializers.SerializerMethodField()
    net_amount = serializers.SerializerMethodField()
    payment_status = serializers.SerializerMethodField()

    class Meta:
        model = Order
        fields = [
            "id",
            "tracking_number",
            "recipient_name",
            "recipient_phone",
            "recipient_address",
            "cod",
            "delivery_charge",
            "net_amount",
            "payment_status",
            "status",
        ]

    def get_delivery_charge(self, obj):
        cancellation_statuses = [
            Order.STATUS_CANCELLED,
            Order.STATUS_RETURNING_TO_VENDOR,
            Order.STATUS_RETURNED_TO_VENDOR,
        ]
        if obj.status in cancellation_statuses:
            return obj.ydm_cancelled_charge or 0
        if obj.ydm_delivery_charge is not None:
            return obj.ydm_delivery_charge
        return obj.delivery_charge or 0

    def get_net_amount(self, obj):
        cancellation_statuses = [
            Order.STATUS_CANCELLED,
            Order.STATUS_RETURNING_TO_VENDOR,
            Order.STATUS_RETURNED_TO_VENDOR,
        ]

        if obj.status in cancellation_statuses:
            cancellation_charge = obj.ydm_cancelled_charge or 0
            return -cancellation_charge

        cod = obj.cod_amount or 0
        delivery_charge = self.get_delivery_charge(obj)
        return cod - delivery_charge

    def get_payment_status(self, obj):
        latest_payment = obj.cod_payments.order_by("-created_at").first()
        if latest_payment and latest_payment.status == "Paid":
            return "Paid"
        return "Pending"
