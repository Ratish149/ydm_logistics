from django.db.models import QuerySet

from invoice.models import Invoice, ReportInvoice


def get_invoices_queryset() -> QuerySet[Invoice]:
    """
    Returns pre-optimized queryset for Invoices.
    """
    return Invoice.objects.all().select_related("user", "created_by", "approved_by")


def get_invoice_reports_queryset() -> QuerySet[ReportInvoice]:
    """
    Returns pre-optimized queryset for Invoice Reports.
    """
    return ReportInvoice.objects.all().select_related("invoice", "reported_by")
