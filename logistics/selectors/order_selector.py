from django.db.models import QuerySet

from logistics.models import Order


def get_orders_for_client(user) -> QuerySet[Order]:
    """
    Returns an optimized QuerySet of orders for a specific user.
    Optimized to prefetch status history to avoid N+1 queries.
    """
    return (
        Order.objects.filter(user=user)
        .prefetch_related("status_history")
        .order_by("-created_at")
    )


def get_order_by_tracking(user, tracking_number: str) -> Order | None:
    """
    Returns an order by tracking number, scoped to the user.
    """
    return (
        Order.objects.filter(user=user, tracking_number=tracking_number)
        .prefetch_related("status_history")
        .first()
    )
