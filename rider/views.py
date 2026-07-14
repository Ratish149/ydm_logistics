from decimal import Decimal

from django.contrib.auth import get_user_model
from django.utils import timezone
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters as rest_filters
from rest_framework import generics, status
from rest_framework.exceptions import NotFound, PermissionDenied, ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

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

User = get_user_model()


class RiderCommissionView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        if user.role not in ["YDM_Rider", "YDM_Operator", "YDM_Logistics"]:
            return Response(
                {"detail": "You do not have permission to view rider commissions."},
                status=status.HTTP_403_FORBIDDEN,
            )

        if user.role == "YDM_Rider":
            rider = user
        else:
            rider_id = request.query_params.get("rider")
            if not rider_id:
                return Response(
                    {
                        "detail": "rider query parameter (phone number) is required for non-rider users."
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )
            try:
                rider = User.objects.get(phone_number=rider_id, role="YDM_Rider")
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
        if user.role not in ["YDM_Rider", "YDM_Operator", "YDM_Logistics"]:
            raise PermissionDenied("You do not have permission to view rider payouts.")

        if user.role == "YDM_Rider":
            rider = user
        else:
            rider_id = self.request.query_params.get("rider")
            if not rider_id:
                raise ValidationError({
                    "detail": "rider query parameter (phone number) is required for non-rider users."
                })
            try:
                rider = User.objects.get(phone_number=rider_id, role="YDM_Rider")
            except User.DoesNotExist:
                raise NotFound({"detail": "Rider not found or is not a YDM Rider."})

        return get_rider_payouts_queryset(rider)

    def create(self, request, *args, **kwargs):
        if request.user.role not in ["YDM_Logistics", "YDM_Operator"]:
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
            rider = User.objects.get(phone_number=rider_id, role="YDM_Rider")
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
        if user.role not in ["YDM_Rider", "YDM_Operator", "YDM_Logistics"]:
            return Response(
                {
                    "detail": "You do not have permission to view rider commission statistics."
                },
                status=status.HTTP_403_FORBIDDEN,
            )

        rider_id = request.query_params.get("rider")
        if rider_id:
            try:
                rider = User.objects.get(phone_number=rider_id, role="YDM_Rider")
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
        if user.role not in ["YDM_Rider", "YDM_Operator", "YDM_Logistics"]:
            return Response(
                {
                    "detail": "You do not have permission to view rider package statistics."
                },
                status=status.HTTP_403_FORBIDDEN,
            )

        if user.role == "YDM_Rider":
            rider = user
        else:
            rider_id = request.query_params.get("rider")
            if not rider_id:
                return Response(
                    {
                        "detail": "rider query parameter (phone number) is required for non-rider users."
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )
            try:
                rider = User.objects.get(phone_number=rider_id, role="YDM_Rider")
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
                else today
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
        if user.role not in ["YDM_Rider", "YDM_Operator", "YDM_Logistics"]:
            raise PermissionDenied("You do not have permission to view rider orders.")

        if user.role == "YDM_Rider":
            rider = user
        else:
            rider_id = self.request.query_params.get("rider")
            if not rider_id:
                raise ValidationError({
                    "detail": "rider query parameter (phone number) is required for non-rider users."
                })
            try:
                rider = User.objects.get(phone_number=rider_id, role="YDM_Rider")
            except User.DoesNotExist:
                raise NotFound({"detail": "Rider not found or is not a YDM Rider."})

        return get_rider_orders_queryset(rider)


class RiderCommissionRateListCreateView(generics.ListCreateAPIView):
    queryset = RiderCommissionRate.objects.all().order_by("order_min_amount")
    serializer_class = RiderCommissionRateSerializer
    permission_classes = [IsAuthenticated]

    def check_permissions(self, request):
        super().check_permissions(request)
        if request.user.role not in ["YDM_Operator", "YDM_Logistics", "Admin"]:
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
        if request.user.role not in ["YDM_Operator", "YDM_Logistics", "Admin"]:
            raise PermissionDenied(
                "Only Operators, Logistics staff, or Admins can manage commission rates."
            )


class RiderDailyStatsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        if user.role not in ["YDM_Rider", "YDM_Operator", "YDM_Logistics"]:
            return Response(
                {
                    "detail": "You do not have permission to view rider daily statistics."
                },
                status=status.HTTP_403_FORBIDDEN,
            )

        if user.role == "YDM_Rider":
            rider = user
        else:
            rider_id = request.query_params.get("rider")
            if not rider_id:
                return Response(
                    {
                        "detail": "rider query parameter (phone number) is required for non-rider users."
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )
            try:
                rider = User.objects.get(phone_number=rider_id, role="YDM_Rider")
            except User.DoesNotExist:
                return Response(
                    {"detail": "Rider not found or is not a YDM Rider."},
                    status=status.HTTP_404_NOT_FOUND,
                )

        start_date_str = request.query_params.get("start_date")
        end_date_str = request.query_params.get("end_date")

        if not start_date_str and not end_date_str:
            today = timezone.localdate()
            start_date = today.replace(day=1)
            end_date = today
        else:
            try:
                start_date = (
                    timezone.datetime.strptime(start_date_str, "%Y-%m-%d").date()
                    if start_date_str
                    else None
                )
                end_date = (
                    timezone.datetime.strptime(end_date_str, "%Y-%m-%d").date()
                    if end_date_str
                    else None
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
