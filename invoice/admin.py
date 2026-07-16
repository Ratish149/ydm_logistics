from django.contrib import admin
from unfold.admin import ModelAdmin

from invoice.models import Invoice, ReportInvoice


@admin.register(Invoice)
class InvoiceAdmin(ModelAdmin):
    list_display = [
        "invoice_code",
        "user",
        "created_by",
        "total_amount",
        "paid_amount",
        "due_amount",
        "status",
        "is_approved",
        "created_at",
    ]
    search_fields = [
        "invoice_code",
        "user__username",
        "user__email",
        "created_by__username",
    ]
    list_filter = ["status", "is_approved", "payment_type", "created_at"]


@admin.register(ReportInvoice)
class ReportInvoiceAdmin(ModelAdmin):
    list_display = ["id", "invoice", "reported_by", "created_at"]
    search_fields = ["invoice__invoice_code", "reported_by__username", "comment"]
    list_filter = ["created_at"]
