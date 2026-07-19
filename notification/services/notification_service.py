from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer


def send_order_placed_notification(order) -> None:
    """Broadcasts a WebSocket notification to the 'order_notifications' group when an order is placed."""
    notification_id = None
    try:
        from notification.models import Notification

        notif = Notification.objects.create(
            user=order.user,
            title="New Order Placed",
            message=f"Order {order.tracking_number} has been placed successfully.",
            notification_type=Notification.NOTIFICATION_TYPE_ORDER_PLACED,
            data={
                "order_id": order.id,
                "tracking_number": order.tracking_number,
            },
        )
        notification_id = notif.id
    except Exception as e:
        print(f"[Database Error] Failed to save order placed notification: {e}")

    try:
        channel_layer = get_channel_layer()
        if channel_layer:
            async_to_sync(channel_layer.group_send)(
                "order_notifications",
                {
                    "type": "order.placed",
                    "order": {
                        "notification_id": notification_id,
                        "id": order.id,
                        "tracking_number": order.tracking_number,
                        "message": f"Order {order.tracking_number} has been placed successfully.",
                        "external_order_code": order.external_order_code,
                        "recipient_name": order.recipient_name,
                        "recipient_address": order.recipient_address,
                        "recipient_phone": order.recipient_phone,
                        "cod_amount": float(order.cod_amount)
                        if order.cod_amount
                        else 0.0,
                        "status": order.status,
                        "created_at": order.created_at.isoformat()
                        if order.created_at
                        else None,
                        "created_by": (
                            order.user.get_full_name() or order.user.username
                            if order.user
                            else "Anonymous"
                        ),
                    },
                },
            )
    except Exception as e:
        print(f"[WebSocket Notification Error] Failed to send order notification: {e}")


def send_rider_assigned_notification(order) -> None:
    """Broadcasts a WebSocket notification to the rider's specific group when a rider is assigned to an order."""
    if not order.assigned_rider:
        return

    notification_id = None
    try:
        from notification.models import Notification

        notif = Notification.objects.create(
            user=order.assigned_rider,
            title="New Order Assigned",
            message=f"You have been assigned to order {order.tracking_number}.",
            notification_type=Notification.NOTIFICATION_TYPE_RIDER_ASSIGNED,
            data={
                "order_id": order.id,
                "tracking_number": order.tracking_number,
                "recipient_address": order.recipient_address,
            },
        )
        notification_id = notif.id
    except Exception as e:
        print(f"[Database Error] Failed to save rider assigned notification: {e}")

    try:
        channel_layer = get_channel_layer()
        if channel_layer:
            async_to_sync(channel_layer.group_send)(
                f"rider_notifications_user_{order.assigned_rider.id}",
                {
                    "type": "order.rider_assigned",
                    "order": {
                        "notification_id": notification_id,
                        "id": order.id,
                        "tracking_number": order.tracking_number,
                        "message": f"You have been assigned to order {order.tracking_number}.",
                        "status": order.status,
                        "recipient_name": order.recipient_name,
                        "recipient_address": order.recipient_address,
                        "assigned_rider": (
                            {
                                "id": order.assigned_rider.id,
                                "name": order.assigned_rider.get_full_name()
                                or order.assigned_rider.username,
                                "phone": getattr(
                                    order.assigned_rider, "phone_number", None
                                ),
                            }
                            if order.assigned_rider
                            else None
                        ),
                    },
                },
            )
    except Exception as e:
        print(
            f"[WebSocket Notification Error] Failed to send rider assignment notification: {e}"
        )


def bulk_mark_notifications_as_read(user, notification_ids=None, mark_all=False) -> int:
    """Marks notifications as read. If mark_all is True, marks all for the user."""
    from notification.models import Notification

    queryset = Notification.objects.filter(user=user, is_read=False)
    if not mark_all and notification_ids:
        queryset = queryset.filter(id__in=notification_ids)
    elif not mark_all and not notification_ids:
        return 0

    return queryset.update(is_read=True)


def send_order_status_update_notification(
    order, changed_by, old_status, new_status
) -> None:
    """Sends a notification to the vendor and to ydm admins about a status change by a rider."""
    if not changed_by or getattr(changed_by, "role", None) != "YDM_Rider":
        return

    from notification.models import Notification

    title = "Order Status Updated"
    message = f"Order {order.tracking_number} status updated from {old_status} to {new_status} by rider {changed_by.get_full_name() or changed_by.username}."

    # 1. Save and send to the Vendor (order.user)
    if order.user:
        notification_id_vendor = None
        try:
            notif_vendor = Notification.objects.create(
                user=order.user,
                title=title,
                message=message,
                notification_type=Notification.NOTIFICATION_TYPE_STATUS_UPDATED,
                data={
                    "order_id": order.id,
                    "tracking_number": order.tracking_number,
                    "old_status": old_status,
                    "new_status": new_status,
                    "changed_by": changed_by.get_full_name() or changed_by.username,
                },
            )
            notification_id_vendor = notif_vendor.id
        except Exception as e:
            print(
                f"[Database Error] Failed to save status update notification for vendor: {e}"
            )

        try:
            channel_layer = get_channel_layer()
            if channel_layer:
                async_to_sync(channel_layer.group_send)(
                    f"rider_notifications_user_{order.user.id}",
                    {
                        "type": "order.status_updated",
                        "order": {
                            "notification_id": notification_id_vendor,
                            "id": order.id,
                            "tracking_number": order.tracking_number,
                            "message": message,
                            "old_status": old_status,
                            "new_status": new_status,
                            "changed_by": changed_by.get_full_name()
                            or changed_by.username,
                        },
                    },
                )
        except Exception as e:
            print(
                f"[WebSocket Notification Error] Failed to send status update to vendor: {e}"
            )

    # 2. Save and send to YDM admin group
    notification_id_ydm = None
    try:
        notif_ydm = Notification.objects.create(
            user=None,
            title=title,
            message=message,
            notification_type=Notification.NOTIFICATION_TYPE_STATUS_UPDATED,
            data={
                "order_id": order.id,
                "tracking_number": order.tracking_number,
                "old_status": old_status,
                "new_status": new_status,
                "changed_by": changed_by.get_full_name() or changed_by.username,
            },
        )
        notification_id_ydm = notif_ydm.id
    except Exception as e:
        print(
            f"[Database Error] Failed to save status update notification for YDM: {e}"
        )

    try:
        channel_layer = get_channel_layer()
        if channel_layer:
            async_to_sync(channel_layer.group_send)(
                "order_notifications",
                {
                    "type": "order.status_updated",
                    "order": {
                        "notification_id": notification_id_ydm,
                        "id": order.id,
                        "tracking_number": order.tracking_number,
                        "message": message,
                        "old_status": old_status,
                        "new_status": new_status,
                        "changed_by": changed_by.get_full_name() or changed_by.username,
                    },
                },
            )
    except Exception as e:
        print(
            f"[WebSocket Notification Error] Failed to send status update to YDM: {e}"
        )
