from django.utils import timezone

from invoice.models import Invoice, ReportInvoice


def create_invoice(created_by, **fields) -> Invoice:
    """
    Creates a new Invoice.
    """
    return Invoice.objects.create(created_by=created_by, **fields)


def update_invoice_approval(invoice: Invoice, is_approved: bool, user) -> Invoice:
    """
    Stamps approval metadata and updates invoice status to Paid if approved.
    """
    if is_approved and (not invoice.is_approved or invoice.approved_at is None):
        invoice.is_approved = True
        invoice.approved_at = timezone.now()
        invoice.approved_by = user
        invoice.status = "Paid"
    else:
        invoice.is_approved = is_approved

    invoice.save()
    return invoice


def create_report(reported_by, invoice: Invoice, comment: str) -> ReportInvoice:
    """
    Creates an Invoice Report.
    """
    return ReportInvoice.objects.create(
        invoice=invoice, reported_by=reported_by, comment=comment
    )
