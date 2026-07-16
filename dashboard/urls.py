from django.urls import path

from dashboard.views import (
    OrderCompleteDashboardAPI,
    OrderDailyDeliveredStatsAPI,
    OrderDailyPlacedStatsAPI,
    OrderStatusDashboardAPI,
    PendingCODApiView,
    UserStatementAPIView,
)

urlpatterns = [
    path("dashboard/", OrderStatusDashboardAPI.as_view(), name="order-dashboard"),
    path(
        "dashboard/complete/",
        OrderCompleteDashboardAPI.as_view(),
        name="order-complete-dashboard",
    ),
    path(
        "dashboard/daily/placed/",
        OrderDailyPlacedStatsAPI.as_view(),
        name="order-daily-placed-stats",
    ),
    path(
        "dashboard/daily/delivered/",
        OrderDailyDeliveredStatsAPI.as_view(),
        name="order-daily-delivered-stats",
    ),
    path(
        "user/statement/",
        UserStatementAPIView.as_view(),
        name="user-statement",
    ),
    path("pending-cod/", PendingCODApiView.as_view(), name="pending-cod"),
]
