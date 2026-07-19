from datetime import datetime, timedelta

from django.contrib.auth import get_user_model
from django.db import models
from django.db.models import Count, Sum
from django.db.models.functions import Coalesce, TruncDate
from django.utils import timezone

from invoice.models import Invoice
from logistics.models import (
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
                "status": "Order Verified",
                "key": Order.STATUS_ORDER_VERIFIED,
                "nos": 0,
                "amount": 0.0,
            },
            {
                "status": "Received At Office",
                "key": Order.STATUS_RECEIVED_AT_OFFICE,
                "nos": 0,
                "amount": 0.0,
            },
            {
                "status": "Ready for Dispatch",
                "key": Order.STATUS_READY_FOR_DISPATCH,
                "nos": 0,
                "amount": 0.0,
            },
        ],
        "order_dispatched": [
            {
                "status": "Order Dispatched",
                "key": Order.STATUS_ORDER_DISPATCHED,
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
            {
                "status": "On Hold",
                "key": Order.STATUS_ON_HOLD,
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
                "status": "Returning to Vendor",
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

    total_rtv = get_status_info([
        Order.STATUS_RETURNING_TO_VENDOR,
        Order.STATUS_RETURNED_TO_VENDOR,
    ])

    # 2. Delivery Charges and Cancellation Charges
    valid_charge = (
        orders.filter(status=Order.STATUS_DELIVERED).aggregate(
            total=Sum("ydm_delivery_charge")
        )["total"]
        or 0.0
    )
    cancelled_charge = (
        orders.filter(
            status__in=[
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
        Invoice.objects
        .filter(user_id=query_user_id, is_approved=True)
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
        todays_logs
        .filter(new_status=Order.STATUS_ORDER_PLACED)
        .values("order_id")
        .distinct()
        .count()
    )
    todays_delivered = (
        todays_logs
        .filter(new_status=Order.STATUS_DELIVERED)
        .values("order_id")
        .distinct()
        .count()
    )
    todays_rescheduled = (
        todays_logs
        .filter(new_status=Order.STATUS_RESCHEDULED)
        .values("order_id")
        .distinct()
        .count()
    )
    todays_rtv = (
        todays_logs
        .filter(
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
                "nos": orders.filter(
                    status=Order.STATUS_DELIVERED,
                    ydm_delivery_charge__isnull=False,
                ).count(),
                "amount": float(valid_charge),
            },
            "total_cancellation_charge": {
                "nos": orders.filter(
                    status__in=[
                        Order.STATUS_CANCELLED,
                        Order.STATUS_RETURNING_TO_VENDOR,
                        Order.STATUS_RETURNED_TO_VENDOR,
                    ],
                    ydm_cancelled_charge__isnull=False,
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


def get_date_range(filter=None, start_date=None, end_date=None):
    today = timezone.now().date()
    if start_date:
        try:
            if isinstance(start_date, str):
                start = datetime.strptime(start_date, "%Y-%m-%d").date()
            else:
                start = start_date
        except ValueError:
            start = today.replace(day=1)
        try:
            if isinstance(end_date, str):
                end = datetime.strptime(end_date, "%Y-%m-%d").date()
            elif end_date:
                end = end_date
            else:
                end = today
        except ValueError:
            end = today
    elif filter == "weekly":
        start = today - timedelta(days=6)
        end = today
    else:  # filter == "monthly" or default
        start = today.replace(day=1)
        end = today
    return start, end


def get_daily_placed_order_stats(
    user=None, target_user_id=None, filter=None, start_date=None, end_date=None
) -> list:
    """
    Returns daily stats of placed orders grouped by date, within the specified filter range.
    """
    query_user_id = target_user_id
    if not query_user_id and user:
        query_user_id = user.id

    start, end = get_date_range(filter, start_date, end_date)

    daily_aggregates = (
        OrderChangeLog.objects
        .filter(
            order__user_id=query_user_id,
            new_status=Order.STATUS_ORDER_PLACED,
            changed_at__date__range=[start, end],
        )
        .annotate(change_date=TruncDate("changed_at"))
        .values("change_date")
        .annotate(count=Count("order_id", distinct=True))
        .order_by("change_date")
    )

    # Generate all dates in the range to fill in zeros
    date_map = {}
    curr = start
    while curr <= end:
        date_map[curr] = 0
        curr += timedelta(days=1)

    for row in daily_aggregates:
        date_map[row["change_date"]] = row["count"]

    return [{"date": d, "placed_count": date_map[d]} for d in sorted(date_map.keys())]


def get_daily_delivered_order_stats(
    user=None, target_user_id=None, filter=None, start_date=None, end_date=None
) -> list:
    """
    Returns daily stats of delivered orders grouped by date, within the specified filter range.
    """
    query_user_id = target_user_id
    if not query_user_id and user:
        query_user_id = user.id

    start, end = get_date_range(filter, start_date, end_date)

    daily_aggregates = (
        OrderChangeLog.objects
        .filter(
            order__user_id=query_user_id,
            new_status=Order.STATUS_DELIVERED,
            changed_at__date__range=[start, end],
        )
        .annotate(change_date=TruncDate("changed_at"))
        .values("change_date")
        .annotate(count=Count("order_id", distinct=True))
        .order_by("change_date")
    )

    # Generate all dates in the range to fill in zeros
    date_map = {}
    curr = start
    while curr <= end:
        date_map[curr] = 0
        curr += timedelta(days=1)

    for row in daily_aggregates:
        date_map[row["change_date"]] = row["count"]

    return [
        {"date": d, "delivered_count": date_map[d]} for d in sorted(date_map.keys())
    ]


def calculate_dashboard_pending_cod(user_id) -> dict:
    orders = Order.objects.filter(user_id=user_id)
    delivered_orders = orders.filter(status=Order.STATUS_DELIVERED)
    cancelled_orders = orders.filter(
        status__in=[
            Order.STATUS_CANCELLED,
            Order.STATUS_RETURNING_TO_VENDOR,
            Order.STATUS_RETURNED_TO_VENDOR,
        ]
    )

    delivered_amount = float(
        delivered_orders.aggregate(total=Sum("cod_amount"))["total"] or 0.0
    )
    total_order = orders.count()
    total_amount = float(orders.aggregate(total=Sum("cod_amount"))["total"] or 0.0)

    delivered_count = delivered_orders.count()
    cancelled_count = cancelled_orders.count()

    valid_charge = float(
        delivered_orders.aggregate(total=Sum("ydm_delivery_charge"))["total"] or 0.0
    )
    cancelled_charge = float(
        cancelled_orders.aggregate(total=Sum("ydm_cancelled_charge"))["total"] or 0.0
    )
    total_charge = valid_charge + cancelled_charge

    approved_paid = (
        Invoice.objects.filter(user_id=user_id, is_approved=True).aggregate(
            total=Sum("paid_amount")
        )["total"]
        or 0.0
    )

    pending_cod = max(
        0.0, float(delivered_amount) - float(total_charge) - float(approved_paid)
    )

    return {
        "pending_cod": pending_cod,
        "delivered_amount": float(delivered_amount),
        "total_order": total_order,
        "total_amount": float(total_amount),
        "total_charge": float(total_charge),
        "approved_paid": float(approved_paid),
        "delivered_count": delivered_count,
        "cancelled_count": cancelled_count,
    }


def generate_order_tracking_statement_optimized(
    user_id, start_date, end_date, dashboard_data=None
) -> list:
    # 1. Historical balance before start_date
    delivered_before_ids = list(
        OrderChangeLog.objects
        .filter(
            order__user_id=user_id,
            new_status=Order.STATUS_DELIVERED,
            changed_at__date__lt=start_date,
        )
        .values_list("order_id", flat=True)
        .distinct()
    )

    delivered_before_orders = Order.objects.filter(id__in=delivered_before_ids)
    hist_cash_in = (
        delivered_before_orders.aggregate(total=Sum("cod_amount"))["total"] or 0.0
    )
    hist_delivery_charge = (
        delivered_before_orders.aggregate(total=Sum("ydm_delivery_charge"))["total"]
        or 0.0
    )

    cancelled_before_ids = list(
        OrderChangeLog.objects
        .filter(
            order__user_id=user_id,
            new_status__in=[
                Order.STATUS_CANCELLED,
                Order.STATUS_RETURNING_TO_VENDOR,
                Order.STATUS_RETURNED_TO_VENDOR,
            ],
            changed_at__date__lt=start_date,
        )
        .values_list("order_id", flat=True)
        .distinct()
    )
    cancelled_before_orders = Order.objects.filter(id__in=cancelled_before_ids)
    hist_cancelled_charge = (
        cancelled_before_orders.aggregate(total=Sum("ydm_cancelled_charge"))["total"]
        or 0.0
    )

    hist_payments = (
        Invoice.objects.filter(
            user_id=user_id,
            is_approved=True,
            approved_at__date__lt=start_date,
        ).aggregate(total=Sum("paid_amount"))["total"]
        or 0.0
    )

    running_balance = (
        float(hist_cash_in)
        - float(hist_delivery_charge)
        - float(hist_cancelled_charge)
        - float(hist_payments)
    )

    # 2. Get range data
    placed_orders = (
        Order.objects
        .filter(
            user_id=user_id,
            created_at__date__range=[start_date, end_date],
        )
        .values("created_at__date")
        .annotate(count=Count("id"), amount=Sum("cod_amount"))
    )
    placed_map = {
        row["created_at__date"]: {
            "count": row["count"],
            "amount": float(row["amount"] or 0.0),
        }
        for row in placed_orders
    }

    delivered_logs = (
        OrderChangeLog.objects
        .filter(
            order__user_id=user_id,
            new_status=Order.STATUS_DELIVERED,
            changed_at__date__range=[start_date, end_date],
        )
        .select_related("order")
        .order_by("changed_at")
    )

    cancelled_logs = (
        OrderChangeLog.objects
        .filter(
            order__user_id=user_id,
            new_status__in=[
                Order.STATUS_CANCELLED,
                Order.STATUS_RETURNING_TO_VENDOR,
                Order.STATUS_RETURNED_TO_VENDOR,
            ],
            changed_at__date__range=[start_date, end_date],
        )
        .select_related("order")
        .order_by("changed_at")
    )

    delivered_map = {}
    seen_delivered_orders = set()
    for log in delivered_logs:
        d = log.changed_at.date()
        if log.order_id in seen_delivered_orders:
            continue
        seen_delivered_orders.add(log.order_id)
        if d not in delivered_map:
            delivered_map[d] = {"count": 0, "delivered_amount": 0.0, "charge": 0.0}
        delivered_map[d]["count"] += 1
        delivered_map[d]["delivered_amount"] += float(log.order.cod_amount or 0.0)
        delivered_map[d]["charge"] += float(log.order.ydm_delivery_charge or 0.0)

    cancelled_map = {}
    seen_cancelled_orders = set()
    for log in cancelled_logs:
        d = log.changed_at.date()
        if log.order_id in seen_cancelled_orders:
            continue
        seen_cancelled_orders.add(log.order_id)
        if d not in cancelled_map:
            cancelled_map[d] = {"charge": 0.0}
        cancelled_map[d]["charge"] += float(log.order.ydm_cancelled_charge or 0.0)

    payments = (
        Invoice.objects
        .filter(
            user_id=user_id,
            is_approved=True,
            approved_at__date__range=[start_date, end_date],
        )
        .values("approved_at__date")
        .annotate(amount=Sum("paid_amount"))
    )
    payments_map = {
        row["approved_at__date"]: float(row["amount"] or 0.0) for row in payments
    }

    # 3. Accumulate day-by-day
    statement_data = []
    curr = start_date
    while curr <= end_date:
        placed = placed_map.get(curr, {"count": 0, "amount": 0.0})
        deliv = delivered_map.get(curr, {"count": 0, "delivered_amount": 0.0, "charge": 0.0})
        canc = cancelled_map.get(curr, {"charge": 0.0})

        day_charge = deliv["charge"] + canc["charge"]
        pay = payments_map.get(curr, 0.0)

        running_balance += deliv["delivered_amount"] - day_charge - pay

        # Only append if there is actual activity on this day
        if (
            placed["count"] > 0
            or deliv["count"] > 0
            or day_charge > 0
            or pay > 0
        ):
            statement_data.append({
                "date": curr,
                "total_order": placed["count"],
                "total_amount": placed["amount"],
                "delivery_count": deliv["count"],
                "delivered_amount": deliv["delivered_amount"],
                "delivery_charge": day_charge,
                "payment": pay,
                "balance": running_balance,
            })
        curr += timedelta(days=1)

    # Sort latest date first
    statement_data.reverse()
    return statement_data


def calculate_just_pending_cod(user_id) -> float:
    """
    Returns only the net pending COD amount for a given user.
    Optimized to run in exactly two database queries (one for Orders, one for Invoices).
    """
    # 1. Gather all order calculations in a single query pass
    order_metrics = Order.objects.filter(user_id=user_id).aggregate(
        delivered_cod=Coalesce(
            Sum("cod_amount", filter=models.Q(status=Order.STATUS_DELIVERED)),
            0.0,
            output_field=models.DecimalField(),
        ),
        delivered_charges=Coalesce(
            Sum("ydm_delivery_charge", filter=models.Q(status=Order.STATUS_DELIVERED)),
            0.0,
            output_field=models.DecimalField(),
        ),
        cancelled_charges=Coalesce(
            Sum(
                "ydm_cancelled_charge",
                filter=models.Q(
                    status__in=[
                        Order.STATUS_CANCELLED,
                        Order.STATUS_RETURNING_TO_VENDOR,
                        Order.STATUS_RETURNED_TO_VENDOR,
                    ]
                ),
            ),
            0.0,
            output_field=models.DecimalField(),
        ),
    )

    # 2. Sum the approved payments
    approved_paid = Invoice.objects.filter(user_id=user_id, is_approved=True).aggregate(
        total=Coalesce(Sum("paid_amount"), 0.0, output_field=models.DecimalField())
    )["total"]

    # 3. Apply the financial formula
    total_charges = (
        order_metrics["delivered_charges"] + order_metrics["cancelled_charges"]
    )
    pending_cod = (
        float(order_metrics["delivered_cod"])
        - float(total_charges)
        - float(approved_paid)
    )

    return max(0.0, pending_cod)
