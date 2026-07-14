from django.urls import path

from invoice.views import (
    InvoiceListCreateView,
    InvoiceReportListCreateView,
    InvoiceReportRetrieveUpdateDestroyView,
    InvoiceRetrieveUpdateDestroyView,
)

urlpatterns = [
    path("invoices/", InvoiceListCreateView.as_view(), name="invoice-list-create"),
    path(
        "invoices/<int:pk>/",
        InvoiceRetrieveUpdateDestroyView.as_view(),
        name="invoice-detail",
    ),
    path(
        "invoices/reports/",
        InvoiceReportListCreateView.as_view(),
        name="invoice-report-list-create",
    ),
    path(
        "invoices/reports/<int:pk>/",
        InvoiceReportRetrieveUpdateDestroyView.as_view(),
        name="invoice-report-detail",
    ),
]
