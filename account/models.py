from django.conf import settings
from django.contrib.auth.models import AbstractUser
from django.db import models


class CustomUser(AbstractUser):
    ROLE_YDM = "ydm"
    ROLE_VENDOR = "vendor"
    ROLE_RIDER = "YDM_Rider"

    ROLE_CHOICES = [
        (ROLE_YDM, "YDM"),
        (ROLE_VENDOR, "Vendor"),
        (ROLE_RIDER, "YDM Rider"),
    ]

    phone_number = models.CharField(max_length=20, blank=True, null=True)
    address = models.TextField(blank=True, null=True)
    role = models.CharField(
        max_length=20,
        choices=ROLE_CHOICES,
        default=ROLE_VENDOR,
        db_index=True,
    )


    class Meta:
        verbose_name = "User"
        verbose_name_plural = "Users"


class APIKey(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="api_keys",
    )
    key = models.CharField(max_length=255, unique=True, db_index=True)
    is_active = models.BooleanField(default=True, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField(null=True, blank=True, db_index=True)
    webhook_url = models.URLField(
        max_length=500,
        null=True,
        blank=True,
        help_text="URL to POST shipment status change events to.",
    )

    class Meta:
        indexes = [
            models.Index(fields=["key", "is_active"]),
            models.Index(fields=["user", "is_active"]),
        ]

    def __str__(self):
        return f"API Key for {self.user.username} (key: {self.key})"
