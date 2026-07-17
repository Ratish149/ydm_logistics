from datetime import datetime

from django.utils import timezone
from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.authentication import JWTAuthentication

from account.authentication import APIKeyAuthentication
from dashboard.selectors import (
    calculate_dashboard_pending_cod,
    calculate_just_pending_cod,
    generate_order_tracking_statement_optimized,
    get_complete_dashboard_stats,
    get_daily_delivered_order_stats,
    get_daily_placed_order_stats,
    get_order_dashboard_stats,
)
from dashboard.serializers import UserStatementSerializer
from ydm.utils.pagination import CustomPagination


class OrderStatusDashboardAPI(APIView):
    authentication_classes = [JWTAuthentication, APIKeyAuthentication]
    permission_classes = []

    def get(self, request):
        target_user_id = request.query_params.get("user_id")

        if target_user_id:
            stats = get_order_dashboard_stats(target_user_id=target_user_id)
            return Response(stats, status=status.HTTP_200_OK)

        if request.user and request.user.is_authenticated and request.user.is_active:
            stats = get_order_dashboard_stats(user=request.user)
            return Response(stats, status=status.HTTP_200_OK)

        return Response(
            {
                "detail": (
                    "Authentication credentials were not provided, and no"
                    " user_id was specified."
                )
            },
            status=status.HTTP_401_UNAUTHORIZED,
        )


class OrderCompleteDashboardAPI(APIView):
    authentication_classes = [JWTAuthentication, APIKeyAuthentication]
    permission_classes = []

    def get(self, request):
        target_user_id = request.query_params.get("user_id")

        if target_user_id:
            stats = get_complete_dashboard_stats(target_user_id=target_user_id)
            return Response(stats, status=status.HTTP_200_OK)

        if request.user and request.user.is_authenticated and request.user.is_active:
            stats = get_complete_dashboard_stats(user=request.user)
            return Response(stats, status=status.HTTP_200_OK)

        return Response(
            {
                "detail": (
                    "Authentication credentials were not provided, and no"
                    " user_id was specified."
                )
            },
            status=status.HTTP_401_UNAUTHORIZED,
        )


class OrderDailyPlacedStatsAPI(APIView):
    authentication_classes = [JWTAuthentication, APIKeyAuthentication]
    permission_classes = []

    def get(self, request):
        target_user_id = request.query_params.get("user_id")
        filter_val = request.query_params.get("filter")
        start_date = request.query_params.get("start_date")
        end_date = request.query_params.get("end_date")

        kwargs = {
            "filter": filter_val,
            "start_date": start_date,
            "end_date": end_date,
        }

        if target_user_id:
            stats = get_daily_placed_order_stats(
                target_user_id=target_user_id, **kwargs
            )
            return Response(stats, status=status.HTTP_200_OK)

        if request.user and request.user.is_authenticated and request.user.is_active:
            stats = get_daily_placed_order_stats(user=request.user, **kwargs)
            return Response(stats, status=status.HTTP_200_OK)

        return Response(
            {
                "detail": (
                    "Authentication credentials were not provided, and no"
                    " user_id was specified."
                )
            },
            status=status.HTTP_401_UNAUTHORIZED,
        )


class OrderDailyDeliveredStatsAPI(APIView):
    authentication_classes = [JWTAuthentication, APIKeyAuthentication]
    permission_classes = []

    def get(self, request):
        target_user_id = request.query_params.get("user_id")
        filter_val = request.query_params.get("filter")
        start_date = request.query_params.get("start_date")
        end_date = request.query_params.get("end_date")

        kwargs = {
            "filter": filter_val,
            "start_date": start_date,
            "end_date": end_date,
        }

        if target_user_id:
            stats = get_daily_delivered_order_stats(
                target_user_id=target_user_id, **kwargs
            )
            return Response(stats, status=status.HTTP_200_OK)

        if request.user and request.user.is_authenticated and request.user.is_active:
            stats = get_daily_delivered_order_stats(user=request.user, **kwargs)
            return Response(stats, status=status.HTTP_200_OK)

        return Response(
            {
                "detail": (
                    "Authentication credentials were not provided, and no"
                    " user_id was specified."
                )
            },
            status=status.HTTP_401_UNAUTHORIZED,
        )


class UserStatementAPIView(generics.ListAPIView):
    serializer_class = UserStatementSerializer
    pagination_class = CustomPagination
    authentication_classes = [JWTAuthentication, APIKeyAuthentication]
    permission_classes = []

    def get_queryset(self):
        return []

    def list(self, request, *args, **kwargs):
        user_id = request.query_params.get("user_id")
        if not user_id:
            if request.user and request.user.is_authenticated:
                user_id = request.user.id
            else:
                return Response(
                    {
                        "error": (
                            "Authentication is required, or user_id must be"
                            " provided as query parameter."
                        )
                    },
                    status=status.HTTP_401_UNAUTHORIZED,
                )

        # 1. Parse date filters
        start_date_param = request.query_params.get("start_date")
        end_date_param = request.query_params.get("end_date")

        if start_date_param and end_date_param:
            try:
                start_date = datetime.strptime(start_date_param, "%Y-%m-%d").date()
                end_date = datetime.strptime(end_date_param, "%Y-%m-%d").date()
            except ValueError:
                return Response(
                    {"error": "Invalid date format. Use YYYY-MM-DD"}, status=400
                )
        else:
            # Default: current calendar month (1st → today)
            today = timezone.now().date()
            start_date = today.replace(day=1)
            end_date = today

        # 2. Dashboard summary
        dashboard_data = calculate_dashboard_pending_cod(user_id)

        # 3. Build statement (optimized)
        statement_data = generate_order_tracking_statement_optimized(
            user_id, start_date, end_date, dashboard_data
        )

        # 4. Apply pagination
        paginator = self.pagination_class()
        paginated_statement = paginator.paginate_queryset(
            statement_data, request, view=self
        )

        serializer = self.serializer_class(paginated_statement, many=True)

        # 5. Return paginated response (DRF style)
        return paginator.get_paginated_response({
            "user_id": user_id,
            "start_date": start_date.strftime("%Y-%m-%d"),
            "end_date": end_date.strftime("%Y-%m-%d"),
            "dashboard_pending_cod": float(dashboard_data["pending_cod"]),
            "dashboard_breakdown": {
                "delivered_amount": float(dashboard_data["delivered_amount"]),
                "total_order": dashboard_data["total_order"],
                "total_amount": float(dashboard_data["total_amount"]),
                "total_charge": float(dashboard_data["total_charge"]),
                "approved_paid": float(dashboard_data["approved_paid"]),
                "delivered_count": dashboard_data["delivered_count"],
                "cancelled_count": dashboard_data["cancelled_count"],
            },
            "statement": serializer.data,
        })


class PendingCODApiView(APIView):
    authentication_classes = [JWTAuthentication, APIKeyAuthentication]
    permission_classes = []

    def get(self, request, *args, **kwargs):
        # Fall back to a target_user_id query param if provided, otherwise use current user
        user_id = request.query_params.get("user_id")

        pending_cod_amount = calculate_just_pending_cod(user_id)

        return Response(
            {"user_id": int(user_id), "pending_cod_amount": pending_cod_amount},
            status=status.HTTP_200_OK,
        )
