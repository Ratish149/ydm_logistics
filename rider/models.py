from django.conf import settings
from django.db import models


class RiderCommissionRate(models.Model):
    order_min_amount = models.DecimalField(max_digits=10, decimal_places=2)
    order_max_amount = models.DecimalField(
        max_digits=10, decimal_places=2, null=True, blank=True
    )
    commission_amount = models.DecimalField(max_digits=10, decimal_places=2)

    class Meta:
        ordering = ["order_min_amount"]

    def __str__(self):
        max_str = (
            f"{self.order_max_amount}" if self.order_max_amount is not None else "Above"
        )
        return f"Order Amount {self.order_min_amount} - {max_str} : Commission {self.commission_amount}"


class RiderPayout(models.Model):
    rider = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="rider_payouts",
        limit_choices_to={"role": "YDM_Rider"},
    )
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    paid_at = models.DateTimeField(auto_now_add=True)
    remarks = models.TextField(blank=True, null=True)

    class Meta:
        ordering = ["-paid_at"]

    def __str__(self):
        return f"{self.rider.username if self.rider else 'Unknown'} - {self.amount} on {self.paid_at.date()}"
