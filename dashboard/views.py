from datetime import datetime

from django.db.models import Max, Min
from django.utils import timezone
from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.authentication import JWTAuthentication

from account.authentication import APIKeyAuthentication
from dashboard.selectors import (
    calculate_dashboard_pending_cod,
    generate_order_tracking_statement_optimized,
    get_complete_dashboard_stats,
    get_daily_delivered_order_stats,
    get_daily_placed_order_stats,
    get_order_dashboard_stats,
)
from dashboard.serializers import UserStatementSerializer
from invoice.models import Invoice
from logistics.models import Order, OrderChangeLog
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
            # fallback: detect earliest and latest activity based on our model
            earliest_order_created = Order.objects.filter(user_id=user_id).aggregate(
                Min("created_at")
            )["created_at__min"]

            earliest_log_sent = OrderChangeLog.objects.filter(
                order__user_id=user_id,
                new_status=Order.STATUS_ORDER_PLACED,
            ).aggregate(Min("changed_at"))["changed_at__min"]

            earliest_delivery = OrderChangeLog.objects.filter(
                order__user_id=user_id,
                new_status=Order.STATUS_DELIVERED,
            ).aggregate(Min("changed_at"))["changed_at__min"]

            earliest_payment = Invoice.objects.filter(
                user_id=user_id, is_approved=True
            ).aggregate(Min("approved_at"))["approved_at__min"]

            latest_activity = max(
                filter(
                    None,
                    [
                        OrderChangeLog.objects.filter(
                            order__user_id=user_id,
                        ).aggregate(Max("changed_at"))["changed_at__max"],
                        Invoice.objects.filter(
                            user_id=user_id, is_approved=True
                        ).aggregate(Max("approved_at"))["approved_at__max"],
                    ],
                ),
                default=timezone.now(),
            )

            start_date_val = min(
                filter(
                    None,
                    [
                        earliest_order_created,
                        earliest_log_sent,
                        earliest_delivery,
                        earliest_payment,
                    ],
                ),
                default=timezone.now(),
            )
            start_date = (
                start_date_val.date()
                if isinstance(start_date_val, datetime)
                else start_date_val
            )
            end_date = (
                latest_activity.date()
                if isinstance(latest_activity, datetime)
                else latest_activity
            )

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
