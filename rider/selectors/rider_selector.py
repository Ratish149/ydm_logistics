from datetime import date

from django.db.models import Count, QuerySet, Sum
from django.db.models.functions import TruncDate

from account.models import CustomUser
from logistics.models import Order, OrderChangeLog
from rider.models import RiderCommissionRate, RiderPayout


def calculate_order_commission(amount: float, rates: list) -> float:
    """
    Calculates rider commission for an order amount based on slabs.
    """
    if rates:
        for rate in rates:
            if rate.order_min_amount <= amount and (
                rate.order_max_amount is None or amount <= rate.order_max_amount
            ):
                return float(rate.commission_amount)
    else:
        # Fallback default rules
        if amount <= 199:
            return 0.0
        elif 200 <= amount <= 249:
            return 25.0
        elif 250 <= amount <= 349:
            return 30.0
        elif 350 <= amount <= 449:
            return 35.0
        else:
            return 40.0
    return 0.0


def get_rider_commission_data(rider: CustomUser) -> dict:
    """
    Calculates detailed commission list, payout records, and summary balance.
    """
    delivered_orders = Order.objects.filter(
        assigned_rider=rider,
        status=Order.STATUS_DELIVERED,
    )

    orders_data = []
    total_commission_earned = 0.0

    rates = list(RiderCommissionRate.objects.all().order_by("order_min_amount"))

    for order in delivered_orders:
        amount = float(order.cod_amount)
        commission = calculate_order_commission(amount, rates)
        total_commission_earned += commission
        orders_data.append({
            "order_id": order.id,
            "tracking_number": order.tracking_number,
            "recipient_name": order.recipient_name,
            "cod_amount": amount,
            "status": order.status,
            "delivery_date": order.delivered_at,
            "commission": commission,
        })

    payouts = RiderPayout.objects.filter(rider=rider)
    total_payout = payouts.aggregate(total=Sum("amount"))["total"] or 0.0
    total_payout = float(total_payout)

    payouts_data = [
        {
            "id": payout.id,
            "amount": float(payout.amount),
            "paid_at": payout.paid_at,
            "remarks": payout.remarks,
        }
        for payout in payouts
    ]

    remaining_balance = total_commission_earned - total_payout

    return {
        "summary": {
            "total_delivered_orders": len(orders_data),
            "total_commission_earned": total_commission_earned,
            "total_commission_paid": total_payout,
            "remaining_balance": remaining_balance,
        },
        "delivered_orders": orders_data,
        "payouts": payouts_data,
    }


def get_rider_payouts_queryset(rider: CustomUser) -> QuerySet[RiderPayout]:
    """
    Returns payouts queryset for a specific rider.
    """
    return RiderPayout.objects.filter(rider=rider).order_by("-paid_at")


def get_rider_commission_stats(rider: CustomUser) -> dict:
    """
    Returns high level lifetime stats for the rider.
    """
    delivered_orders = Order.objects.filter(
        assigned_rider=rider,
        status=Order.STATUS_DELIVERED,
    )
    num_orders = delivered_orders.count()

    rates = list(RiderCommissionRate.objects.all().order_by("order_min_amount"))
    commission_per_order = 0.0
    if rates:
        for rate in rates:
            if rate.order_min_amount <= num_orders and (
                rate.order_max_amount is None or num_orders <= rate.order_max_amount
            ):
                commission_per_order = float(rate.commission_amount)
                break
    else:
        if num_orders <= 199:
            commission_per_order = 0.0
        elif 200 <= num_orders <= 249:
            commission_per_order = 25.0
        elif 250 <= num_orders <= 349:
            commission_per_order = 30.0
        elif 350 <= num_orders <= 449:
            commission_per_order = 35.0
        else:
            commission_per_order = 40.0

    lifetime_commission_earned = num_orders * commission_per_order

    payouts = RiderPayout.objects.filter(rider=rider)
    total_payout = payouts.aggregate(total=Sum("amount"))["total"] or 0.0
    total_payout = float(total_payout)
    remaining_balance = lifetime_commission_earned - total_payout

    return {
        "lifetime_commission_earned": lifetime_commission_earned,
        "lifetime_commission_paid": total_payout,
        "remaining_balance": remaining_balance,
    }


def get_rider_package_stats(
    rider: CustomUser, start_date: date, end_date: date
) -> dict:
    """
    Returns range-specific package counts and lifetime totals.
    """
    total_assigned_in_range = Order.objects.filter(
        assigned_rider=rider,
        created_at__date__gte=start_date,
        created_at__date__lte=end_date,
    ).count()

    total_delivered_in_range = Order.objects.filter(
        assigned_rider=rider,
        status=Order.STATUS_DELIVERED,
        created_at__date__gte=start_date,
        created_at__date__lte=end_date,
    ).count()

    lifetime_delivered_count = Order.objects.filter(
        assigned_rider=rider, status=Order.STATUS_DELIVERED
    ).count()

    lifetime_cancelled_count = Order.objects.filter(
        assigned_rider=rider, status=Order.STATUS_CANCELLED
    ).count()

    return {
        "packages_assigned": total_assigned_in_range,
        "packages_delivered": total_delivered_in_range,
        "total_packages_delivered_lifetime": lifetime_delivered_count,
        "total_packages_cancelled_lifetime": lifetime_cancelled_count,
    }


def get_rider_orders_queryset(rider: CustomUser) -> QuerySet[Order]:
    """
    Returns pre-optimized Order queryset for the rider.
    """
    return (
        Order.objects
        .filter(assigned_rider=rider)
        .select_related("user", "assigned_rider")
        .prefetch_related("change_logs", "comments")
        .order_by("-id")
    )


def get_rider_daily_stats(rider: CustomUser, start_date: date, end_date: date) -> list:
    """
    Aggregates delivered and cancelled daily counts.
    """
    delivered_logs = OrderChangeLog.objects.filter(
        order__assigned_rider=rider,
        new_status=Order.STATUS_DELIVERED,
    )

    return_statuses = [
        Order.STATUS_CANCELLED,
        Order.STATUS_RETURNING_TO_VENDOR,
        Order.STATUS_RETURNED_TO_VENDOR,
    ]
    returned_logs = OrderChangeLog.objects.filter(
        order__assigned_rider=rider,
        new_status__in=return_statuses,
    )

    if start_date:
        delivered_logs = delivered_logs.filter(changed_at__date__gte=start_date)
        returned_logs = returned_logs.filter(changed_at__date__gte=start_date)
    if end_date:
        delivered_logs = delivered_logs.filter(changed_at__date__lte=end_date)
        returned_logs = returned_logs.filter(changed_at__date__lte=end_date)

    delivered_counts = (
        delivered_logs
        .annotate(date=TruncDate("changed_at"))
        .values("date")
        .annotate(count=Count("order_id", distinct=True))
        .values_list("date", "count")
    )
    delivered_map = {row[0]: row[1] for row in delivered_counts}

    returned_counts = (
        returned_logs
        .annotate(date=TruncDate("changed_at"))
        .values("date")
        .annotate(count=Count("order_id", distinct=True))
        .values_list("date", "count")
    )
    returned_map = {row[0]: row[1] for row in returned_counts}

    all_dates = sorted(
        set(delivered_map.keys()) | set(returned_map.keys()), reverse=True
    )

    results = []
    for d in all_dates:
        results.append({
            "date": d.strftime("%Y-%m-%d") if d else None,
            "delivered_count": delivered_map.get(d, 0),
            "returned_count": returned_map.get(d, 0),
        })

    return results
