from django.contrib import admin
from django.contrib.auth import get_user_model
from django.contrib.auth.admin import UserAdmin
from unfold.admin import ModelAdmin

from account.models import APIKey
from account.services import api_key_service

User = get_user_model()


@admin.register(User)
class CustomUserAdmin(UserAdmin, ModelAdmin):
    fieldsets = UserAdmin.fieldsets + (
        ("Additional Info", {"fields": ("phone_number", "address", "role")}),
    )
    add_fieldsets = UserAdmin.add_fieldsets + (
        ("Additional Info", {"fields": ("phone_number", "address", "role")}),
    )
    list_display = UserAdmin.list_display + ("phone_number", "role")


@admin.register(APIKey)
class APIKeyAdmin(ModelAdmin):
    list_display = (
        "user",
        "key",
        "is_active",
        "expires_at",
        "created_at",
    )
    search_fields = ("user__username", "user__first_name", "key")
    list_filter = ("is_active", "expires_at")
    raw_id_fields = ("user",)
    readonly_fields = ("key",)

    def save_model(self, request, obj, form, change):
        if not obj.key:
            api_key_service.generate_key_for_obj(obj)
        super().save_model(request, obj, form, change)
