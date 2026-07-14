from django.urls import path

from rider.views import (
    RiderCommissionRateListCreateView,
    RiderCommissionRateRetrieveUpdateDestroyView,
    RiderCommissionStatsView,
    RiderCommissionView,
    RiderDailyStatsView,
    RiderOrdersListView,
    RiderPackageStatsView,
    RiderPayoutView,
)

urlpatterns = [
    path(
        "rider/commissions/",
        RiderCommissionView.as_view(),
        name="rider-commissions",
    ),
    path(
        "rider/commissions/stats/",
        RiderCommissionStatsView.as_view(),
        name="rider-commission-stats",
    ),
    path(
        "rider/packages/stats/",
        RiderPackageStatsView.as_view(),
        name="rider-package-stats",
    ),
    path(
        "rider/orders/",
        RiderOrdersListView.as_view(),
        name="rider-orders-list",
    ),
    path(
        "rider/payouts/",
        RiderPayoutView.as_view(),
        name="rider-payouts",
    ),
    path(
        "rider/commission-rates/",
        RiderCommissionRateListCreateView.as_view(),
        name="rider-commission-rates-list-create",
    ),
    path(
        "rider/commission-rates/<int:pk>/",
        RiderCommissionRateRetrieveUpdateDestroyView.as_view(),
        name="rider-commission-rates-detail",
    ),
    path(
        "rider/daily-stats/",
        RiderDailyStatsView.as_view(),
        name="rider-daily-stats",
    ),
]
