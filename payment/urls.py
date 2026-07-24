from django.urls import path

from payment.views import (
    CodPaymentListCreateAPIView,
    CodPaymentOrdersListAPIView,
    CodPaymentRetrieveUpdateDestroyAPIView,
    DeliveryBillPaymentListCreateAPIView,
    DeliveryBillPaymentOrdersListAPIView,
    DeliveryBillPaymentRetrieveUpdateDestroyAPIView,
    UnpaidCodOrdersListAPIView,
    UnpaidDeliveryBillOrdersListAPIView,
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
    path(
        "delivery-bill/",
        DeliveryBillPaymentListCreateAPIView.as_view(),
        name="delivery-bill-list-create",
    ),
    path(
        "delivery-bill/orders/",
        DeliveryBillPaymentOrdersListAPIView.as_view(),
        name="delivery-bill-orders-list",
    ),
    path(
        "delivery-bill/unpaid-orders/",
        UnpaidDeliveryBillOrdersListAPIView.as_view(),
        name="unpaid-delivery-bill-orders-list",
    ),
    path(
        "delivery-bill/<int:pk>/",
        DeliveryBillPaymentRetrieveUpdateDestroyAPIView.as_view(),
        name="delivery-bill-detail",
    ),
]
