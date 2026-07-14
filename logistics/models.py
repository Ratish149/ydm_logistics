from django.conf import settings
from django.db import models


class Order(models.Model):
    STATUS_ORDER_PLACED = "ORDER_PLACED"
    STATUS_ORDER_VERIFIED = "ORDER_VERIFIED"
    STATUS_READY_FOR_DISPATCH = "READY_FOR_DISPATCH"
    STATUS_RECEIVED_AT_OFFICE = "RECEIVED_AT_OFFICE"
    STATUS_ORDER_DISPATCHED = "ORDER_DISPATCHED"
    STATUS_OUT_FOR_DELIVERY = "OUT_FOR_DELIVERY"
    STATUS_RESCHEDULED = "RESCHEDULED"
    STATUS_DELIVERED = "DELIVERED"
    STATUS_CANCELLED = "CANCELLED"
    STATUS_RETURNING_TO_VENDOR = "RETURNING_TO_VENDOR"
    STATUS_RETURNED_TO_VENDOR = "RETURNED_TO_VENDOR"
    STATUS_ON_HOLD = "ON_HOLD"

    STATUS_CHOICES = [
        (STATUS_ORDER_PLACED, "Order Placed"),
        (STATUS_ORDER_VERIFIED, "Order Verified"),
        (STATUS_RECEIVED_AT_OFFICE, "Received At Office"),
        (STATUS_READY_FOR_DISPATCH, "Ready for Dispatch"),
        (STATUS_ORDER_DISPATCHED, "Order Dispatched"),
        (STATUS_OUT_FOR_DELIVERY, "Out For Delivery"),
        (STATUS_RESCHEDULED, "Rescheduled"),
        (STATUS_DELIVERED, "Delivered"),
        (STATUS_CANCELLED, "Cancelled"),
        (STATUS_RETURNING_TO_VENDOR, "Returning to Vendor"),
        (STATUS_RETURNED_TO_VENDOR, "Returned to Vendor"),
        (STATUS_ON_HOLD, "On Hold"),
    ]

    PAYMENT_TYPE_PREPAID = "PREPAID"
    PAYMENT_TYPE_COD = "COD"

    PAYMENT_TYPE_CHOICES = [
        (PAYMENT_TYPE_PREPAID, "Prepaid"),
        (PAYMENT_TYPE_COD, "Cash on Delivery"),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="orders",
        db_index=True,
    )
    tracking_number = models.CharField(max_length=50, unique=True, db_index=True)
    external_order_code = models.CharField(
        max_length=100, db_index=True, blank=True, null=True
    )

    sender_name = models.CharField(max_length=255, blank=True, null=True)
    sender_phone = models.CharField(max_length=50, blank=True, null=True, db_index=True)
    sender_address = models.TextField(blank=True, null=True)
    sender_email = models.EmailField(db_index=True, blank=True, null=True)

    recipient_name = models.CharField(max_length=255)
    recipient_phone = models.CharField(max_length=50, db_index=True)
    recipient_email = models.EmailField(db_index=True, blank=True, null=True)
    recipient_address = models.TextField()
    recipient_city = models.CharField(
        max_length=100, blank=True, null=True, db_index=True
    )
    recipient_district = models.CharField(
        max_length=100, blank=True, null=True, db_index=True
    )

    cod_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.0)
    delivery_charge = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    payment_type = models.CharField(
        max_length=20,
        choices=PAYMENT_TYPE_CHOICES,
        default=PAYMENT_TYPE_COD,
        db_index=True,
    )
    product = models.JSONField(blank=True, null=True)
    special_instructions = models.TextField(blank=True, null=True)

    # Scheduling
    pickup_date = models.DateTimeField(null=True, blank=True)
    delivered_at = models.DateTimeField(null=True, blank=True)

    # Delivery tracking
    delivery_attempts = models.PositiveSmallIntegerField(default=0)
    assigned_rider = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="assigned_orders",
        db_index=True,
    )

    status = models.CharField(
        max_length=50,
        choices=STATUS_CHOICES,
        default=STATUS_ORDER_PLACED,
        db_index=True,
    )
    remarks = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [
            models.Index(fields=["user", "status"]),
            models.Index(fields=["user", "created_at"]),
            models.Index(fields=["status", "payment_type"]),
            models.Index(fields=["assigned_rider", "status"]),
            models.Index(fields=["recipient_city", "status"]),
        ]

    def __str__(self):
        return f"{self.tracking_number} - {self.recipient_name} ({self.status})"


class OrderStatusHistory(models.Model):
    order = models.ForeignKey(
        Order, on_delete=models.CASCADE, related_name="status_history"
    )
    status = models.CharField(max_length=50, choices=Order.STATUS_CHOICES)
    changed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="status_changes",
    )
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["order", "created_at"]),
        ]

    def __str__(self):
        return f"{self.order.tracking_number} -> {self.status} by {self.changed_by} at {self.created_at}"


class OrderComment(models.Model):
    COMMENT_TYPE_GENERAL = "GENERAL"
    COMMENT_TYPE_FAILURE = "FAILURE"
    COMMENT_TYPE_CANCELLATION = "CANCELLATION"
    COMMENT_TYPE_HOLD = "HOLD"
    COMMENT_TYPE_RESCHEDULE = "RESCHEDULE"

    COMMENT_TYPE_CHOICES = [
        (COMMENT_TYPE_GENERAL, "General"),
        (COMMENT_TYPE_FAILURE, "Failure Reason"),
        (COMMENT_TYPE_CANCELLATION, "Cancellation Reason"),
        (COMMENT_TYPE_HOLD, "Hold Reason"),
        (COMMENT_TYPE_RESCHEDULE, "Reschedule Reason"),
    ]

    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="comments")
    commented_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name="order_comments",
        db_index=True,
    )
    comment_type = models.CharField(
        max_length=20,
        choices=COMMENT_TYPE_CHOICES,
        default=COMMENT_TYPE_GENERAL,
        db_index=True,
    )
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["order", "comment_type"]),
            models.Index(fields=["order", "created_at"]),
        ]

    def __str__(self):
        return (
            f"{self.order.tracking_number} - {self.comment_type} by {self.commented_by}"
        )


class OrderChangeLog(models.Model):
    order = models.ForeignKey(
        Order, on_delete=models.CASCADE, related_name="change_logs"
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, null=True, blank=True
    )
    old_status = models.CharField(max_length=255)
    new_status = models.CharField(max_length=255)
    comment = models.TextField(null=True, blank=True)
    changed_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["changed_at"]
        indexes = [
            models.Index(fields=["order", "changed_at"]),
            models.Index(fields=["user", "changed_at"]),
            models.Index(fields=["new_status", "changed_at"]),
        ]

    def __str__(self):
        return f"{self.order.tracking_number} - {self.old_status} → {self.new_status}"


class AssignOrder(models.Model):
    order = models.ForeignKey(
        Order, on_delete=models.CASCADE, related_name="assign_orders"
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="rider_assignments",
    )
    assigned_at = models.DateTimeField(auto_now_add=True)
    is_rider_verified = models.BooleanField(default=False)
    ydm_delivery_charge = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Logistics delivery charge set by the rider based on delivery address (separate from franchise delivery_charge)",
    )

    DELIVERY_LOCATION_CHOICES = (
        ("Inside Ringroad", "Inside Ringroad"),
        ("Outside Ringroad", "Outside Ringroad"),
    )
    delivery_location_type = models.CharField(
        max_length=50,
        choices=DELIVERY_LOCATION_CHOICES,
        null=True,
        blank=True,
        db_index=True,
        help_text="Delivery location type selected by the rider (Inside Ringroad or Outside Ringroad).",
    )

    ydm_cancelled_charge = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Logistics cancelled charge set when the order is assigned or updated (separate from franchise delivery_charge)",
    )

    class Meta:
        ordering = ["-assigned_at"]
        indexes = [
            models.Index(fields=["order", "-assigned_at"]),
            models.Index(fields=["user", "-assigned_at"]),
        ]

    def __str__(self):
        return f"{self.user.username if self.user else 'No Rider'} - {self.order.tracking_number}"


class YdmLogisticsSetting(models.Model):
    inside_ringroad_charge = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=100.00,
        help_text="YDM delivery charge for inside ringroad deliveries.",
    )
    outside_ringroad_charge = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=150.00,
        help_text="YDM delivery charge for outside ringroad deliveries.",
    )
    cancelled_charge = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0.00,
        help_text="YDM charge for cancelled / returned deliveries.",
    )

    class Meta:
        verbose_name = "YDM Logistics Setting"
        verbose_name_plural = "YDM Logistics Settings"

    def __str__(self):
        return f"Inside: {self.inside_ringroad_charge}, Outside: {self.outside_ringroad_charge}, Cancelled: {self.cancelled_charge}"

    def save(self, *args, **kwargs):
        self.pk = 1
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        pass  # Prevent deletion of the singleton instance

    @classmethod
    def load(cls):
        obj, _ = cls.objects.get_or_create(
            pk=1,
            defaults={
                "inside_ringroad_charge": 100.00,
                "outside_ringroad_charge": 150.00,
                "cancelled_charge": 0.00,
            },
        )
        return obj
