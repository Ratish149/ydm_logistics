import random
import string

from django.contrib.auth import get_user_model
from django.db import transaction

from logistics.models import Order, OrderChangeLog, OrderComment

User = get_user_model()


def generate_tracking_number() -> str:
    """Generates a unique tracking number, e.g., YDM-A8B9C2"""
    code = "".join(random.choices(string.ascii_uppercase + string.digits, k=6))
    return f"YDM-{code}"


@transaction.atomic
def create_order(
    user,
    recipient_name: str,
    recipient_address: str,
    recipient_phone: str,
    external_order_code: str = None,
    sender_name: str = None,
    sender_phone: str = None,
    sender_address: str = None,
    sender_email: str = None,
    recipient_email: str = None,
    recipient_city: str = None,
    recipient_district: str = None,
    cod_amount: float = 0.0,
    delivery_charge: float = 0.0,
    payment_type: str = Order.PAYMENT_TYPE_COD,
    product=None,
    special_instructions: str = None,
    pickup_date=None,
    delivered_at=None,
    assigned_rider=None,
    remarks: str = None,
) -> Order:
    # Default sender details from the authenticated user (API key owner)
    if not sender_name:
        if user and not user.is_anonymous:
            full_name = f"{user.first_name} {user.last_name}".strip()
            sender_name = full_name or user.username
        else:
            sender_name = "Anonymous"
    if not sender_phone:
        sender_phone = (
            getattr(user, "phone_number", None)
            if user and not user.is_anonymous
            else None
        )
    if not sender_address:
        sender_address = (
            getattr(user, "address", None) if user and not user.is_anonymous else None
        )
    if not sender_email:
        sender_email = (user.email or None) if user and not user.is_anonymous else None

    # Generate unique tracking number
    tracking_number = generate_tracking_number()
    while Order.objects.filter(tracking_number=tracking_number).exists():
        tracking_number = generate_tracking_number()

    order = Order.objects.create(
        user=user,
        tracking_number=tracking_number,
        external_order_code=external_order_code,
        sender_name=sender_name,
        sender_phone=sender_phone,
        sender_address=sender_address,
        sender_email=sender_email,
        recipient_name=recipient_name,
        recipient_address=recipient_address,
        recipient_phone=recipient_phone,
        recipient_email=recipient_email,
        recipient_city=recipient_city,
        recipient_district=recipient_district,
        cod_amount=cod_amount,
        delivery_charge=delivery_charge,
        payment_type=payment_type,
        product=product,
        special_instructions=special_instructions,
        pickup_date=pickup_date,
        delivered_at=delivered_at,
        assigned_rider=assigned_rider,
        remarks=remarks,
        status=Order.STATUS_ORDER_PLACED,
    )

    # Initial history record via ChangeLog
    OrderChangeLog.objects.create(
        order=order,
        user=user,
        old_status="",
        new_status=Order.STATUS_ORDER_PLACED,
        comment="Order Placed",
    )

    return order


def handle_order_status_change(
    order: Order, old_status: str, new_status: str, changed_by=None, comment: str = None
):
    if old_status == new_status:
        return

    from logistics.models import YdmLogisticsSetting

    # 1. Create the OrderChangeLog
    OrderChangeLog.objects.create(
        order=order,
        user=changed_by,
        old_status=old_status,
        new_status=new_status,
        comment=comment,
    )

    # 2. if order status is change to cancelled status then add the cancellation charge from YdmLogisticsSetting
    if new_status == Order.STATUS_CANCELLED:
        setting = YdmLogisticsSetting.load()
        order.ydm_cancelled_charge = setting.cancelled_charge
        order.save(update_fields=["ydm_cancelled_charge"])

    # 3. and if order is change from cancelled to other status then remove the cancellation charge
    elif old_status == Order.STATUS_CANCELLED:
        order.ydm_cancelled_charge = None
        order.save(update_fields=["ydm_cancelled_charge"])


@transaction.atomic
def update_order_status(
    order: Order,
    new_status: str,
    changed_by=None,
    webhook_url: str = None,
    comment: str = None,
) -> Order:
    old_status = order.status
    print(
        f"[YDM Status Change] Order {order.tracking_number}: '{old_status}' -> '{new_status}' (changed_by: {changed_by}, comment: {comment})"
    )
    if old_status != new_status:
        order.status = new_status
        order.save(update_fields=["status", "updated_at"])
        handle_order_status_change(order, old_status, new_status, changed_by, comment)
        print(
            f"[YDM Status Change] Saved status for {order.tracking_number} successfully."
        )

    # Fire webhook after the transaction commits so the DB state is consistent
    from logistics.services.webhook_service import fire_status_change_webhook

    def on_commit_callback():
        print(
            f"[YDM Webhook] Transaction committed. Firing webhook to '{webhook_url}' for order {order.tracking_number} (status: {new_status})"
        )
        fire_status_change_webhook(order, new_status, webhook_url)
        print(
            f"[YDM Webhook] Webhook invocation completed for order {order.tracking_number}."
        )

    transaction.on_commit(on_commit_callback)

    return order


@transaction.atomic
def create_order_comment(
    order: Order,
    commented_by,
    message: str,
) -> OrderComment:
    return OrderComment.objects.create(
        order=order,
        commented_by=commented_by,
        message=message,
    )
