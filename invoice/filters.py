from django_filters import rest_framework as django_filters

from invoice.models import Invoice, ReportInvoice


class InvoiceFilter(django_filters.FilterSet):
    payment_type = django_filters.CharFilter(
        field_name="payment_type", lookup_expr="exact"
    )
    status = django_filters.CharFilter(field_name="status", lookup_expr="exact")
    is_approved = django_filters.BooleanFilter(
        field_name="is_approved", lookup_expr="exact"
    )

    class Meta:
        model = Invoice
        fields = [
            "payment_type",
            "status",
            "is_approved",
        ]


class InvoiceReportFilter(django_filters.FilterSet):
    invoice = django_filters.CharFilter(field_name="invoice__id", lookup_expr="exact")

    class Meta:
        model = ReportInvoice
        fields = [
            "invoice",
        ]
