from django.urls import path

from dashboard.views import (
    FranchiseStatementAPIView,
    OrderCompleteDashboardAPI,
    OrderDailyDeliveredStatsAPI,
    OrderDailyPlacedStatsAPI,
    OrderStatusDashboardAPI,
)

urlpatterns = [
    path(
        "orders/dashboard/", OrderStatusDashboardAPI.as_view(), name="order-dashboard"
    ),
    path(
        "orders/dashboard/complete/",
        OrderCompleteDashboardAPI.as_view(),
        name="order-complete-dashboard",
    ),
    path(
        "orders/dashboard/daily/placed/",
        OrderDailyPlacedStatsAPI.as_view(),
        name="order-daily-placed-stats",
    ),
    path(
        "orders/dashboard/daily/delivered/",
        OrderDailyDeliveredStatsAPI.as_view(),
        name="order-daily-delivered-stats",
    ),
    path(
        "franchise/statement/",
        FranchiseStatementAPIView.as_view(),
        name="franchise-statement",
    ),
]
