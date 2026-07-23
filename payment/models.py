from django.conf import settings
from django.db import models


class CodPayment(models.Model):
    STATUS_CHOICES = (
        ("Pending", "Pending"),
        ("Paid", "Paid"),
    )

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="cod_payments",
        db_index=True,
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="created_cod_payments",
        null=True,
        blank=True,
        db_index=True,
    )
    orders = models.ManyToManyField(
        "logistics.Order",
        related_name="cod_payments",
        blank=True,
    )
    payment_number = models.CharField(
        max_length=100, unique=True, db_index=True, null=True, blank=True
    )
    delivery_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    total_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    status = models.CharField(
        max_length=20, choices=STATUS_CHOICES, default="Pending", db_index=True
    )

    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["user", "status"]),
            models.Index(fields=["created_at", "status"]),
        ]

    def __str__(self):
        return f"CodPayment {self.payment_number or self.id} - {self.user.username} ({self.status})"

    def save(self, *args, **kwargs):
        is_new = self.pk is None
        super().save(*args, **kwargs)
        if is_new and not self.payment_number:
            self.payment_number = f"PAY-{self.pk:05d}"
            super().save(update_fields=["payment_number"])
