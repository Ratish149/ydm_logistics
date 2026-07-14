from collections import defaultdict

from django.contrib.auth import get_user_model
from django.db import models
from django.db.models import Count, Sum
from django.db.models.functions import Coalesce, TruncDate
from django.utils import timezone

from invoice.models import Invoice
from logistics.models import (
    AssignOrder,
    Order,
    OrderChangeLog,
)

User = get_user_model()


def get_order_dashboard_stats(user=None, target_user_id=None) -> dict:
    """
    Aggregates order count and total COD amount grouped by status.
    If target_user_id is provided, it prioritizes filtering by user_id.
    Otherwise, it filters by the user object.
    """
    if target_user_id:
        orders_queryset = Order.objects.filter(user_id=target_user_id)
    elif user:
        orders_queryset = Order.objects.filter(user=user)
    else:
        orders_queryset = Order.objects.none()

    # Aggregated query grouped by status
    db_stats = orders_queryset.values("status").annotate(
        nos=Count("id"),
        amount=Coalesce(Sum("cod_amount"), 0.0, output_field=models.DecimalField()),
    )

    stats_map = {item["status"]: item for item in db_stats}

    # Initialize standard groups with keys, default counts, and amounts
    groups = {
        "order_processing": [
            {
                "status": "Order Placed",
                "key": Order.STATUS_ORDER_PLACED,
                "nos": 0,
                "amount": 0.0,
            },
            {
                "status": "Order Picked",
                "key": Order.STATUS_ORDER_DISPATCHED,
                "nos": 0,
                "amount": 0.0,
            },
            {
                "status": "Order Verified",
                "key": Order.STATUS_ORDER_VERIFIED,
                "nos": 0,
                "amount": 0.0,
            },
            {
                "status": "Order Processing",
                "key": Order.STATUS_READY_FOR_DISPATCH,
                "nos": 0,
                "amount": 0.0,
            },
        ],
        "order_dispatched": [
            {
                "status": "Received At Branch",
                "key": Order.STATUS_RECEIVED_AT_OFFICE,
                "nos": 0,
                "amount": 0.0,
            },
            {
                "status": "Out For Delivery",
                "key": Order.STATUS_OUT_FOR_DELIVERY,
                "nos": 0,
                "amount": 0.0,
            },
            {
                "status": "Rescheduled",
                "key": Order.STATUS_RESCHEDULED,
                "nos": 0,
                "amount": 0.0,
            },
        ],
        "order_status": [
            {
                "status": "Delivered",
                "key": Order.STATUS_DELIVERED,
                "nos": 0,
                "amount": 0.0,
            },
            {
                "status": "Cancelled",
                "key": Order.STATUS_CANCELLED,
                "nos": 0,
                "amount": 0.0,
            },
            {
                "status": "Pending RTV",
                "key": Order.STATUS_RETURNING_TO_VENDOR,
                "nos": 0,
                "amount": 0.0,
            },
            {
                "status": "Returned to Vendor",
                "key": Order.STATUS_RETURNED_TO_VENDOR,
                "nos": 0,
                "amount": 0.0,
            },
            {
                "status": "On Hold",
                "key": Order.STATUS_ON_HOLD,
                "nos": 0,
                "amount": 0.0,
            },
        ],
    }

    # Populate groups with data from DB
    for group_name, items in groups.items():
        for item in items:
            key = item["key"]
            if key in stats_map:
                item["nos"] = stats_map[key]["nos"]
                item["amount"] = float(stats_map[key]["amount"])

    return groups


def get_complete_dashboard_stats(user=None, target_user_id=None) -> dict:
    """
    Returns complete dashboard statistics:
    - total_order, total_cod, total_rtv, total_delivery_charge, total_pending_cod, last_cod_payment,
      today's stats, and delivery performance.
    """
    query_user_id = target_user_id
    if not query_user_id and user:
        query_user_id = user.id

    orders = Order.objects.filter(user_id=query_user_id)

    # 1. Overall aggregations per status
    status_aggregates = orders.values("status").annotate(
        count=Count("id"),
        total_cod=Sum("cod_amount"),
    )
    stats_by_status = {
        row["status"]: {
            "count": row["count"],
            "total_cod": float(row["total_cod"] or 0.0),
        }
        for row in status_aggregates
    }

    def get_status_info(statuses):
        if isinstance(statuses, str):
            statuses = [statuses]
        total_count = 0
        total_amount = 0.0
        for status_label in statuses:
            st = stats_by_status.get(status_label)
            if st:
                total_count += st["count"]
                total_amount += st["total_cod"]
        return {"nos": total_count, "amount": total_amount}

    # Total Orders (all active states)
    all_statuses = [
        Order.STATUS_ORDER_PLACED,
        Order.STATUS_ORDER_VERIFIED,
        Order.STATUS_RECEIVED_AT_OFFICE,
        Order.STATUS_READY_FOR_DISPATCH,
        Order.STATUS_ORDER_DISPATCHED,
        Order.STATUS_OUT_FOR_DELIVERY,
        Order.STATUS_RESCHEDULED,
        Order.STATUS_DELIVERED,
        Order.STATUS_CANCELLED,
        Order.STATUS_RETURNING_TO_VENDOR,
        Order.STATUS_RETURNED_TO_VENDOR,
        Order.STATUS_ON_HOLD,
    ]
    total_orders = get_status_info(all_statuses)

    # Total COD (non-cancelled, non-rtv)
    active_cod_statuses = [
        Order.STATUS_ORDER_PLACED,
        Order.STATUS_ORDER_VERIFIED,
        Order.STATUS_RECEIVED_AT_OFFICE,
        Order.STATUS_READY_FOR_DISPATCH,
        Order.STATUS_ORDER_DISPATCHED,
        Order.STATUS_OUT_FOR_DELIVERY,
        Order.STATUS_RESCHEDULED,
        Order.STATUS_DELIVERED,
    ]
    total_cod = get_status_info(active_cod_statuses)

    total_rtv = get_status_info(
        [
            Order.STATUS_RETURNING_TO_VENDOR,
            Order.STATUS_RETURNED_TO_VENDOR,
        ]
    )

    # 2. Delivery Charges and Cancellation Charges
    assign_order_qs = AssignOrder.objects.filter(order__user_id=query_user_id)
    valid_charge = (
        assign_order_qs.filter(order__status=Order.STATUS_DELIVERED).aggregate(
            total=Sum("ydm_delivery_charge")
        )["total"]
        or 0.0
    )
    cancelled_charge = (
        assign_order_qs.filter(
            order__status__in=[
                Order.STATUS_CANCELLED,
                Order.STATUS_RETURNING_TO_VENDOR,
                Order.STATUS_RETURNED_TO_VENDOR,
            ]
        ).aggregate(total=Sum("ydm_cancelled_charge"))["total"]
        or 0.0
    )

    # 3. Pending COD
    delivered_stats = get_status_info(Order.STATUS_DELIVERED)
    approved_paid = (
        Invoice.objects.filter(user_id=query_user_id, is_approved=True).aggregate(
            total=Sum("paid_amount")
        )["total"]
        or 0.0
    )
    pending_cod_amount = max(
        0.0,
        float(delivered_stats["amount"])
        - float(valid_charge)
        - float(cancelled_charge)
        - float(approved_paid),
    )

    # 4. Last COD Payment (from approved invoices)
    last_invoice = (
        Invoice.objects.filter(user_id=query_user_id, is_approved=True)
        .order_by("-approved_at")
        .first()
    )
    last_cod_payment = (
        {
            "amount": float(last_invoice.paid_amount or 0.0),
            "date": last_invoice.approved_at,
        }
        if last_invoice
        else None
    )

    # 5. Today's stats from OrderChangeLog
    today = timezone.now().date()
    todays_logs = OrderChangeLog.objects.filter(
        changed_at__date=today, order__user_id=query_user_id
    )
    todays_placed = (
        todays_logs.filter(new_status=Order.STATUS_ORDER_PLACED)
        .values("order_id")
        .distinct()
        .count()
    )
    todays_delivered = (
        todays_logs.filter(new_status=Order.STATUS_DELIVERED)
        .values("order_id")
        .distinct()
        .count()
    )
    todays_rescheduled = (
        todays_logs.filter(new_status=Order.STATUS_RESCHEDULED)
        .values("order_id")
        .distinct()
        .count()
    )
    todays_rtv = (
        todays_logs.filter(
            new_status__in=[
                Order.STATUS_CANCELLED,
                Order.STATUS_RETURNING_TO_VENDOR,
                Order.STATUS_RETURNED_TO_VENDOR,
            ]
        )
        .values("order_id")
        .distinct()
        .count()
    )

    # 6. Delivery Performance
    delivered_count = delivered_stats["nos"]
    cancelled_count = get_status_info(Order.STATUS_CANCELLED)["nos"]
    returned_vendor_count = total_rtv["nos"]
    completed_orders = delivered_count + cancelled_count + returned_vendor_count

    delivered_percentage = (
        round((delivered_count / completed_orders) * 100, 2)
        if completed_orders > 0
        else 0.0
    )
    cancelled_percentage = (
        round(((cancelled_count + returned_vendor_count) / completed_orders) * 100, 2)
        if completed_orders > 0
        else 0.0
    )

    return {
        "overall_statistics": {
            "total_order": total_orders,
            "total_cod": total_cod,
            "total_delivered": delivered_stats,
            "total_rtv": total_rtv,
            "total_delivery_charge": {
                "nos": assign_order_qs.filter(
                    order__status=Order.STATUS_DELIVERED
                ).count(),
                "amount": float(valid_charge),
            },
            "total_cancellation_charge": {
                "nos": assign_order_qs.filter(
                    order__status__in=[
                        Order.STATUS_CANCELLED,
                        Order.STATUS_RETURNING_TO_VENDOR,
                        Order.STATUS_RETURNED_TO_VENDOR,
                    ]
                ).count(),
                "amount": float(cancelled_charge),
            },
            "total_pending_cod": {
                "nos": delivered_stats["nos"],
                "amount": pending_cod_amount,
            },
            "last_cod_payment": last_cod_payment,
        },
        "todays_statistics": {
            "todays_orders": todays_placed,
            "todays_delivery": todays_delivered,
            "todays_rescheduled": todays_rescheduled,
            "todays_cancellation": todays_rtv,
        },
        "delivery_performance": {
            "delivered_percentage": delivered_percentage,
            "cancelled_percentage": cancelled_percentage,
        },
    }


def get_daily_order_stats(user=None, target_user_id=None) -> list:
    """
    Returns daily stats of placed and delivered orders grouped by date.
    Optimized to query and group using Django ORM to prevent N+1 queries.
    """
    query_user_id = target_user_id
    if not query_user_id and user:
        query_user_id = user.id

    daily_aggregates = (
        OrderChangeLog.objects.filter(
            order__user_id=query_user_id,
            new_status__in=[Order.STATUS_ORDER_PLACED, Order.STATUS_DELIVERED],
        )
        .annotate(change_date=TruncDate("changed_at"))
        .values("change_date", "new_status")
        .annotate(count=Count("order_id", distinct=True))
        .order_by("change_date")
    )

    data_by_date = defaultdict(lambda: {"placed_count": 0, "delivered_count": 0})
    for row in daily_aggregates:
        d = row["change_date"]
        status_val = row["new_status"]
        count = row["count"]
        if status_val == Order.STATUS_ORDER_PLACED:
            data_by_date[d]["placed_count"] = count
        elif status_val == Order.STATUS_DELIVERED:
            data_by_date[d]["delivered_count"] = count

    formatted_stats = []
    for d in sorted(data_by_date.keys()):
        formatted_stats.append(
            {
                "date": d,
                "placed_count": data_by_date[d]["placed_count"],
                "delivered_count": data_by_date[d]["delivered_count"],
            }
        )

    return formatted_stats
