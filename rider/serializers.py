from rest_framework import serializers

from account.serializers import UserListSerializer
from rider.models import RiderCommissionRate, RiderPayout


class RiderCommissionRateSerializer(serializers.ModelSerializer):
    class Meta:
        model = RiderCommissionRate
        fields = [
            "id",
            "order_min_count",
            "order_max_count",
            "commission_amount",
        ]


class RiderPayoutSerializer(serializers.ModelSerializer):
    rider_detail = UserListSerializer(source="rider", read_only=True)

    class Meta:
        model = RiderPayout
        fields = [
            "id",
            "rider",
            "rider_detail",
            "amount",
            "paid_at",
            "remarks",
        ]
        read_only_fields = ["paid_at"]
