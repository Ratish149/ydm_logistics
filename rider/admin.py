from django.contrib import admin
from unfold.admin import ModelAdmin

from rider.models import RiderCommissionRate, RiderPayout


@admin.register(RiderCommissionRate)
class RiderCommissionRateAdmin(ModelAdmin):
    list_display = ["id", "order_min_amount", "order_max_amount", "commission_amount"]
    search_fields = ["order_min_amount", "order_max_amount"]
    list_filter = ["commission_amount"]


@admin.register(RiderPayout)
class RiderPayoutAdmin(ModelAdmin):
    list_display = ["id", "rider", "amount", "paid_at"]
    search_fields = ["rider__username", "rider__email", "rider__phone_number"]
    list_filter = ["paid_at"]
