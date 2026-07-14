from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.authentication import JWTAuthentication

from account.authentication import APIKeyAuthentication
from dashboard.selectors import (
    get_complete_dashboard_stats,
    get_daily_order_stats,
    get_order_dashboard_stats,
)


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


class OrderDailyStatsAPI(APIView):
    authentication_classes = [JWTAuthentication, APIKeyAuthentication]
    permission_classes = []

    def get(self, request):
        target_user_id = request.query_params.get("user_id")

        if target_user_id:
            stats = get_daily_order_stats(target_user_id=target_user_id)
            return Response(stats, status=status.HTTP_200_OK)

        if request.user and request.user.is_authenticated and request.user.is_active:
            stats = get_daily_order_stats(user=request.user)
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
