from django.contrib import admin
from unfold.admin import ModelAdmin

from payment.models import CodPayment


@admin.register(CodPayment)
class CodPaymentAdmin(ModelAdmin):
    list_display = (
        "payment_number",
        "user",
        "delivery_amount",
        "total_amount",
        "status",
        "created_at",
    )
    list_filter = ("status", "created_at")
    search_fields = ("payment_number", "user__username", "user__email")
    filter_horizontal = ("orders",)
