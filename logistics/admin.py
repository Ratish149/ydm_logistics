from django.contrib import admin
from unfold.admin import ModelAdmin, TabularInline

from logistics.models import Order, OrderChangeLog, OrderComment


class OrderChangeLogInline(TabularInline):
    model = OrderChangeLog
    extra = 1
    readonly_fields = ("changed_at",)
    raw_id_fields = ("user",)


class OrderCommentInline(TabularInline):
    model = OrderComment
    extra = 1
    readonly_fields = ("created_at",)


@admin.register(Order)
class OrderAdmin(ModelAdmin):
    list_display = (
        "tracking_number",
        "user",
        "external_order_code",
        "recipient_name",
        "recipient_phone",
        "cod_amount",
        "status",
        "created_at",
    )
    list_filter = ("status", "user", "created_at")
    search_fields = (
        "tracking_number",
        "external_order_code",
        "sender_name",
        "recipient_name",
        "recipient_phone",
    )
    raw_id_fields = ("user", "assigned_rider")
    readonly_fields = ("tracking_number", "created_at", "updated_at")
    inlines = [OrderChangeLogInline, OrderCommentInline]


@admin.register(OrderComment)
class OrderCommentAdmin(ModelAdmin):
    list_display = ("order", "commented_by", "created_at")
    list_filter = ("created_at",)
    search_fields = ("order__tracking_number", "message")
    raw_id_fields = ("order", "commented_by")


@admin.register(OrderChangeLog)
class OrderChangeLogAdmin(ModelAdmin):
    list_display = ("order", "user", "old_status", "new_status", "changed_at")
    list_filter = ("old_status", "new_status", "changed_at")
    search_fields = ("order__tracking_number", "comment")
    raw_id_fields = ("order", "user")
