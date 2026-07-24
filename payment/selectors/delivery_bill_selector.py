from django.db.models import QuerySet

from payment.models import DeliveryBillPayment


def get_delivery_bills_selector(
    user=None, user_id=None
) -> QuerySet[DeliveryBillPayment]:
    """
    Returns pre-optimized DeliveryBillPayment queryset with pre-fetched orders and users.
    - ydm / admin role: can pass user_id to filter by target user, or get all if user_id is None.
    - Vendor: scoped strictly to their own delivery bill payments.
    """
    qs = DeliveryBillPayment.objects.select_related(
        "user", "created_by"
    ).prefetch_related("orders", "orders__change_logs")
    if not user or not user.is_authenticated:
        return DeliveryBillPayment.objects.none()

    from account.models import CustomUser

    if user.role in [CustomUser.ROLE_YDM, "Admin"]:
        if user_id:
            return qs.filter(user_id=user_id)
        return qs

    return qs.filter(user=user)


def get_delivery_bill_orders_selector(user=None, user_id=None):
    """
    Returns Order queryset for orders associated with DeliveryBillPayments.
    - ydm / admin role:
      - If user_id is provided: returns orders linked to that target user's DeliveryBillPayments.
      - If no user_id is provided: returns all orders linked to DeliveryBillPayments.
    - vendor: returns orders linked to DeliveryBillPayments where DeliveryBillPayment.user == authenticated user.
    """

    from account.models import CustomUser
    from logistics.models import Order

    qs = (
        Order.objects
        .select_related("user", "assigned_rider")
        .prefetch_related("change_logs", "delivery_bill_payments")
        .distinct()
        .order_by("-created_at")
    )

    if not user or not user.is_authenticated:
        return Order.objects.none()

    if user.role in [CustomUser.ROLE_YDM, "Admin"]:
        if user_id:
            return qs.filter(delivery_bill_payments__user_id=user_id)
        return qs.filter(delivery_bill_payments__isnull=False)

    return qs.filter(delivery_bill_payments__user=user)


def get_unpaid_delivery_bill_orders_selector(user=None, user_id=None):
    """
    Returns Order queryset for orders where delivery_bill_payments is null (no delivery bill record associated),
    filtered strictly for DELIVERED, CANCELLED, or RETURNED_TO_VENDOR statuses.
    - ydm / admin: if user_id is provided, filters by order owner user_id. If no user_id, returns all matching orders.
    - vendor: returns matching orders belonging to vendor.
    """
    from account.models import CustomUser
    from logistics.models import Order

    allowed_statuses = [
        Order.STATUS_DELIVERED,
        Order.STATUS_CANCELLED,
        Order.STATUS_RETURNED_TO_VENDOR,
    ]

    qs = (
        Order.objects
        .filter(delivery_bill_payments__isnull=True, status__in=allowed_statuses)
        .select_related("user", "assigned_rider")
        .prefetch_related("change_logs")
        .distinct()
        .order_by("-created_at")
    )

    if not user or not user.is_authenticated:
        return Order.objects.none()

    if user.role in [CustomUser.ROLE_YDM, "Admin"]:
        if user_id:
            return qs.filter(user_id=user_id)
        return qs

    return qs.filter(user=user)
