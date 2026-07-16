from django.urls import path

from logistics.views import (
    OrderCommentListCreateAPI,
    OrderDetailAPI,
    OrderExportAPI,
    OrderImportAPI,
    OrderListCreateAPI,
    OrderStatusUpdateAPI,
    OrderTemplateDownloadAPI,
    WebhookConfigAPI,
)

urlpatterns = [
    path("orders/", OrderListCreateAPI.as_view(), name="order-list-create"),
    path(
        "orders/template/",
        OrderTemplateDownloadAPI.as_view(),
        name="order-template-download",
    ),
    path("orders/import/", OrderImportAPI.as_view(), name="order-import"),
    path("orders/export/", OrderExportAPI.as_view(), name="order-export"),
    path(
        "orders/<str:tracking_number>/",
        OrderDetailAPI.as_view(),
        name="order-detail",
    ),
    path(
        "orders/<str:tracking_number>/update-status/",
        OrderStatusUpdateAPI.as_view(),
        name="order-update-status",
    ),
    path(
        "orders/<str:tracking_number>/comments/",
        OrderCommentListCreateAPI.as_view(),
        name="order-comments",
    ),
    path("ydm/webhook/", WebhookConfigAPI.as_view(), name="webhook-config"),
]
