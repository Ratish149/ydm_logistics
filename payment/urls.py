from django.urls import path

from payment.views import (
    CodPaymentListCreateAPIView,
    CodPaymentOrdersListAPIView,
    CodPaymentRetrieveUpdateDestroyAPIView,
    UnpaidCodOrdersListAPIView,
)

urlpatterns = [
    path(
        "payment/",
        CodPaymentListCreateAPIView.as_view(),
        name="cod-payment-list-create",
    ),
    path(
        "payment/orders/",
        CodPaymentOrdersListAPIView.as_view(),
        name="cod-payment-orders-list",
    ),
    path(
        "payment/unpaid-orders/",
        UnpaidCodOrdersListAPIView.as_view(),
        name="unpaid-cod-orders-list",
    ),
    path(
        "payment/<int:pk>/",
        CodPaymentRetrieveUpdateDestroyAPIView.as_view(),
        name="cod-payment-detail",
    ),
]
