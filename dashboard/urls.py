from django.urls import path

from dashboard.views import (
    OrderCompleteDashboardAPI,
    OrderDailyStatsAPI,
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
        "orders/dashboard/daily/",
        OrderDailyStatsAPI.as_view(),
        name="order-daily-stats",
    ),
]
