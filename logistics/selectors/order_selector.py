from django.db.models import QuerySet

from logistics.models import Order


def get_orders_for_client(user) -> QuerySet[Order]:
    """
    Returns an optimized QuerySet of orders.

    Accepts three forms for `user`:
    - A User instance  → filters orders to that specific user (vendor/default).
    - A string/int id  → filters orders to the user with that pk (ydm ?user_id=<id>).
    - None             → returns all orders without a user filter (ydm, no filter).

    Optimized to prefetch change_logs and select related user to avoid N+1 queries.
    """
    qs = (
        Order.objects
        .select_related("user", "assigned_rider")
        .prefetch_related("change_logs")
        .order_by("-created_at")
    )
    if user is None:
        return qs

    from account.models import CustomUser

    if isinstance(user, (str, int)):
        try:
            user_obj = CustomUser.objects.get(pk=user)
        except CustomUser.DoesNotExist:
            return Order.objects.none()
    else:
        user_obj = user

    if user_obj.role == CustomUser.ROLE_RIDER:
        return qs.filter(assigned_rider=user_obj)
    return qs.filter(user=user_obj)


def get_order_by_tracking(tracking_number: str, user=None) -> Order | None:
    """
    Returns an order by tracking number, scoped to the user.
    """
    qs = Order.objects.filter(tracking_number=tracking_number)
    if user is not None:
        qs = qs.filter(user=user)
    return qs.prefetch_related("change_logs").first()
