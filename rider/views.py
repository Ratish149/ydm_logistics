from decimal import Decimal

from django.utils import timezone
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters as rest_filters
from rest_framework import generics, status
from rest_framework.exceptions import NotFound, PermissionDenied, ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from account.models import CustomUser
from account.serializers import UserListSerializer
from logistics.serializers import OrderDetailSerializer
from rider.filters import RiderOrderFilter
from rider.models import RiderCommissionRate
from rider.selectors.rider_selector import (
    get_rider_commission_data,
    get_rider_commission_stats,
    get_rider_daily_stats,
    get_rider_orders_queryset,
    get_rider_package_stats,
    get_rider_payouts_queryset,
)
from rider.serializers import RiderCommissionRateSerializer, RiderPayoutSerializer
from rider.services.rider_service import create_rider_payout
from ydm.utils.pagination import CustomPagination

User = CustomUser


class RiderCommissionView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        if user.role not in ["YDM_Rider", "ydm"]:
            return Response(
                {"detail": "You do not have permission to view rider commissions."},
                status=status.HTTP_403_FORBIDDEN,
            )

        if user.role == "YDM_Rider":
            rider = user
        else:
            rider_id = request.query_params.get("user_id")
            if not rider_id:
                return Response(
                    {
                        "detail": "rider query parameter (id) is required for non-rider users."
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )
            try:
                rider = User.objects.get(id=rider_id, role="YDM_Rider")
            except User.DoesNotExist:
                return Response(
                    {"detail": "Rider not found or is not a YDM Rider."},
                    status=status.HTTP_404_NOT_FOUND,
                )

        data = get_rider_commission_data(rider)
        return Response(
            {
                "rider": UserListSerializer(rider).data,
                **data,
            },
            status=status.HTTP_200_OK,
        )


class RiderPayoutView(generics.ListCreateAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = RiderPayoutSerializer
    pagination_class = CustomPagination

    def get_queryset(self):
        user = self.request.user
        if user.role not in ["YDM_Rider", "ydm"]:
            raise PermissionDenied("You do not have permission to view rider payouts.")

        if user.role == "YDM_Rider":
            rider = user
        else:
            rider_id = self.request.query_params.get("user_id")
            if not rider_id:
                raise ValidationError({
                    "detail": "rider query parameter (phone number) is required for non-rider users."
                })
            try:
                rider = User.objects.get(id=rider_id, role="YDM_Rider")
            except User.DoesNotExist:
                raise NotFound({"detail": "Rider not found or is not a YDM Rider."})

        return get_rider_payouts_queryset(rider)

    def create(self, request, *args, **kwargs):
        if request.user.role not in ["ydm"]:
            return Response(
                {"detail": "You do not have permission to log payouts."},
                status=status.HTTP_403_FORBIDDEN,
            )

        rider_id = request.data.get("rider")
        amount = request.data.get("amount")
        remarks = request.data.get("remarks", "")

        if not rider_id or amount is None:
            return Response(
                {"detail": "rider and amount are required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            rider = User.objects.get(id=rider_id, role="YDM_Rider")
        except User.DoesNotExist:
            return Response(
                {"detail": "Rider not found or is not a YDM Rider."},
                status=status.HTTP_404_NOT_FOUND,
            )

        try:
            amount_decimal = Decimal(str(amount))
            if amount_decimal <= 0:
                raise ValueError
        except Exception:
            return Response(
                {"detail": "Amount must be a positive decimal number."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        payout = create_rider_payout(rider, amount_decimal, remarks)
        serializer = self.get_serializer(payout)
        return Response(
            {
                "detail": "Payout registered successfully.",
                "payout": serializer.data,
            },
            status=status.HTTP_201_CREATED,
        )


class RiderCommissionStatsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        if user.role not in ["YDM_Rider", "ydm"]:
            return Response(
                {
                    "detail": "You do not have permission to view rider commission statistics."
                },
                status=status.HTTP_403_FORBIDDEN,
            )

        rider_id = request.query_params.get("user_id")
        if rider_id:
            try:
                rider = User.objects.get(id=rider_id, role="YDM_Rider")
            except User.DoesNotExist:
                return Response(
                    {"detail": "Rider not found or is not a YDM Rider."},
                    status=status.HTTP_404_NOT_FOUND,
                )
        else:
            if user.role == "YDM_Rider":
                rider = user
            else:
                return Response(
                    {
                        "detail": "rider query parameter (phone number) is required for non-rider users."
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )

        stats = get_rider_commission_stats(rider)
        return Response(stats, status=status.HTTP_200_OK)


class RiderPackageStatsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        if user.role not in ["YDM_Rider", "ydm"]:
            return Response(
                {
                    "detail": "You do not have permission to view rider package statistics."
                },
                status=status.HTTP_403_FORBIDDEN,
            )

        if user.role == "YDM_Rider":
            rider = user
        else:
            rider_id = request.query_params.get("user_id")
            if not rider_id:
                return Response(
                    {
                        "detail": "rider query parameter (phone number) is required for non-rider users."
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )
            try:
                rider = User.objects.get(id=rider_id, role="YDM_Rider")
            except User.DoesNotExist:
                return Response(
                    {"detail": "Rider not found or is not a YDM Rider."},
                    status=status.HTTP_404_NOT_FOUND,
                )

        start_date_str = request.query_params.get("start_date")
        end_date_str = request.query_params.get("end_date")

        start_date = None
        end_date = None

        try:
            if start_date_str:
                start_date = timezone.datetime.strptime(
                    start_date_str, "%Y-%m-%d"
                ).date()
            if end_date_str:
                end_date = timezone.datetime.strptime(end_date_str, "%Y-%m-%d").date()
        except ValueError:
            return Response(
                {
                    "detail": "Invalid date format. Use YYYY-MM-DD for start_date and end_date."
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        stats = get_rider_package_stats(rider, start_date, end_date)
        return Response(stats, status=status.HTTP_200_OK)


class RiderOrdersListView(generics.ListAPIView):
    permission_classes = [IsAuthenticated]
    pagination_class = CustomPagination
    serializer_class = OrderDetailSerializer
    filterset_class = RiderOrderFilter
    filter_backends = [
        DjangoFilterBackend,
        rest_filters.SearchFilter,
        rest_filters.OrderingFilter,
    ]
    search_fields = [
        "recipient_phone",
        "recipient_name",
        "tracking_number",
        "recipient_address",
    ]
    ordering_fields = "__all__"

    def get_queryset(self):
        user = self.request.user
        if user.role not in ["YDM_Rider", "ydm"]:
            raise PermissionDenied("You do not have permission to view rider orders.")

        if user.role == "YDM_Rider":
            rider = user
        else:
            rider_id = self.request.query_params.get("user_id")
            if not rider_id:
                raise ValidationError({
                    "detail": "rider query parameter (phone number) is required for non-rider users."
                })
            try:
                rider = User.objects.get(id=rider_id, role="YDM_Rider")
            except User.DoesNotExist:
                raise NotFound({"detail": "Rider not found or is not a YDM Rider."})

        return get_rider_orders_queryset(rider)


class RiderCommissionRateListCreateView(generics.ListCreateAPIView):
    queryset = RiderCommissionRate.objects.all().order_by("order_min_count")
    serializer_class = RiderCommissionRateSerializer
    permission_classes = [IsAuthenticated]

    def check_permissions(self, request):
        super().check_permissions(request)
        if request.user.role not in ["ydm", "Admin"]:
            raise PermissionDenied(
                "Only Operators, Logistics staff, or Admins can manage commission rates."
            )


class RiderCommissionRateRetrieveUpdateDestroyView(
    generics.RetrieveUpdateDestroyAPIView
):
    queryset = RiderCommissionRate.objects.all()
    serializer_class = RiderCommissionRateSerializer
    permission_classes = [IsAuthenticated]

    def check_permissions(self, request):
        super().check_permissions(request)
        if request.user.role not in ["ydm", "Admin"]:
            raise PermissionDenied(
                "Only Operators, Logistics staff, or Admins can manage commission rates."
            )


class RiderDailyStatsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        if user.role not in ["YDM_Rider", "ydm"]:
            return Response(
                {
                    "detail": "You do not have permission to view rider daily statistics."
                },
                status=status.HTTP_403_FORBIDDEN,
            )

        if user.role == "YDM_Rider":
            rider = user
        else:
            rider_id = request.query_params.get("user_id")
            if not rider_id:
                return Response(
                    {
                        "detail": "rider query parameter (phone number) is required for non-rider users."
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )
            try:
                rider = User.objects.get(id=rider_id, role="YDM_Rider")
            except User.DoesNotExist:
                return Response(
                    {"detail": "Rider not found or is not a YDM Rider."},
                    status=status.HTTP_404_NOT_FOUND,
                )

        start_date_str = request.query_params.get("start_date")
        end_date_str = request.query_params.get("end_date")

        today = timezone.localdate()
        try:
            start_date = (
                timezone.datetime.strptime(start_date_str, "%Y-%m-%d").date()
                if start_date_str
                else today.replace(day=1)
            )
            end_date = (
                timezone.datetime.strptime(end_date_str, "%Y-%m-%d").date()
                if end_date_str
                else today
            )
        except ValueError:
            return Response(
                {
                    "detail": "Invalid date format. Use YYYY-MM-DD for start_date and end_date."
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        results = get_rider_daily_stats(rider, start_date, end_date)
        return Response(results, status=status.HTTP_200_OK)


class RiderOrderVerifyView(APIView):
    """
    POST: Rider verifies an order and sets the delivery location type.
    This only marks is_rider_verified=True and stores delivery_location_type.
    Does NOT change order status.
    """

    permission_classes = [IsAuthenticated]

    def post(self, request, tracking_number):
        user = request.user
        if user.role not in ["YDM_Rider", "ydm"]:
            return Response(
                {"detail": "You do not have permission to verify orders."},
                status=status.HTTP_403_FORBIDDEN,
            )

        from logistics.models import Order

        try:
            order = Order.objects.select_related("assigned_rider").get(
                tracking_number=tracking_number
            )
        except Order.DoesNotExist:
            return Response(
                {"detail": "Order not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        if user.role == "YDM_Rider" and order.assigned_rider != user:
            return Response(
                {"detail": "You are not assigned to this order."},
                status=status.HTTP_403_FORBIDDEN,
            )

        delivery_location_type = request.data.get("delivery_location_type")
        if not delivery_location_type:
            return Response(
                {"detail": "delivery_location_type is required."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if delivery_location_type not in ["Inside Ringroad", "Outside Ringroad"]:
            return Response(
                {
                    "detail": "delivery_location_type must be 'Inside Ringroad' or 'Outside Ringroad'."
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        from logistics.models import YdmLogisticsSetting

        logistics_settings = YdmLogisticsSetting.load()

        if delivery_location_type == "Inside Ringroad":
            order.ydm_delivery_charge = logistics_settings.inside_ringroad_charge
        else:
            order.ydm_delivery_charge = logistics_settings.outside_ringroad_charge

        order.ydm_cancelled_charge = logistics_settings.cancelled_charge
        order.delivery_location_type = delivery_location_type
        order.is_rider_verified = True
        order.save(
            update_fields=[
                "delivery_location_type",
                "is_rider_verified",
                "ydm_delivery_charge",
                "ydm_cancelled_charge",
                "updated_at",
            ]
        )

        return Response(
            {
                "detail": "Order verified successfully.",
                "tracking_number": order.tracking_number,
                "delivery_location_type": order.delivery_location_type,
                "is_rider_verified": order.is_rider_verified,
                "ydm_delivery_charge": order.ydm_delivery_charge,
                "ydm_cancelled_charge": order.ydm_cancelled_charge,
            },
            status=status.HTTP_200_OK,
        )


class RiderOrderStatusUpdateView(APIView):
    """
    POST: Rider changes an order status.
    Riders can only set: DELIVERED, ON_HOLD, RESCHEDULED, CANCELLED.
    A comment is required for ON_HOLD, RESCHEDULED, CANCELLED.
    When DELIVERED, the ydm_delivery_charge is auto-set from YdmLogisticsSetting
    based on delivery_location_type.
    """

    permission_classes = [IsAuthenticated]

    # String literals used here because Order is only imported inside the method
    RIDER_ALLOWED_STATUSES = {
        "DELIVERED",
        "ON_HOLD",
        "RESCHEDULED",
        "CANCELLED",
    }

    COMMENT_REQUIRED_STATUSES = {
        "ON_HOLD",
        "RESCHEDULED",
        "CANCELLED",
    }

    def post(self, request, tracking_number):
        from logistics.models import Order
        from logistics.services.order_service import update_order_status

        user = request.user
        if user.role not in ["YDM_Rider", "ydm"]:
            return Response(
                {"detail": "You do not have permission to update order status."},
                status=status.HTTP_403_FORBIDDEN,
            )

        try:
            order = Order.objects.select_related("assigned_rider").get(
                tracking_number=tracking_number
            )
        except Order.DoesNotExist:
            return Response(
                {"detail": "Order not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        if user.role == "YDM_Rider" and order.assigned_rider != user:
            return Response(
                {"detail": "You are not assigned to this order."},
                status=status.HTTP_403_FORBIDDEN,
            )

        new_status_value = request.data.get("status")
        comment = request.data.get("comment", "").strip()

        if not new_status_value:
            return Response(
                {"detail": "status is required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Riders are restricted to a subset of statuses
        if new_status_value not in self.RIDER_ALLOWED_STATUSES:
            return Response(
                {
                    "detail": (
                        "Riders can only set status to: "
                        f"{', '.join(sorted(self.RIDER_ALLOWED_STATUSES))}."
                    )
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Comment required for hold/reschedule/cancel
        if new_status_value in self.COMMENT_REQUIRED_STATUSES and not comment:
            return Response(
                {
                    "detail": f"A comment is required when setting status to {new_status_value}."
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        # For DELIVERED: set delivered_at timestamp
        if new_status_value == Order.STATUS_DELIVERED:
            from django.utils import timezone

            order.delivered_at = timezone.now()
            order.save(update_fields=["delivered_at", "updated_at"])

        # Resolve webhook URL from the order owner's active API keys
        from account.models import APIKey

        api_key_obj = (
            APIKey.objects
            .filter(user=order.user, is_active=True)
            .exclude(webhook_url="")
            .exclude(webhook_url__isnull=True)
            .first()
        )
        webhook_url = api_key_obj.webhook_url if api_key_obj else None

        update_order_status(
            order,
            new_status_value,
            changed_by=user,
            webhook_url=webhook_url,
            comment=comment or None,
        )

        return Response(
            {
                "detail": "Order status updated successfully.",
                "tracking_number": order.tracking_number,
                "status": new_status_value,
            },
            status=status.HTTP_200_OK,
        )
