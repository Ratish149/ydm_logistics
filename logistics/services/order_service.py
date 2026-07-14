import random
import string

from django.contrib.auth import get_user_model
from django.db import transaction

from logistics.models import Order, OrderComment, OrderStatusHistory

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
        full_name = f"{user.first_name} {user.last_name}".strip()
        sender_name = full_name or user.username
    if not sender_address:
        sender_address = getattr(user, "address", None)
    if not sender_email:
        sender_email = user.email or None

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

    # Initial history record
    OrderStatusHistory.objects.create(
        order=order,
        status=Order.STATUS_ORDER_PLACED,
        changed_by=user,
    )

    return order


@transaction.atomic
def update_order_status(
    order: Order,
    new_status: str,
    changed_by=None,
    webhook_url: str = None,
) -> Order:
    order.status = new_status
    order.save()

    OrderStatusHistory.objects.create(
        order=order,
        status=new_status,
        changed_by=changed_by,
    )

    # Fire webhook after the transaction commits so the DB state is consistent
    from logistics.services.webhook_service import fire_status_change_webhook

    transaction.on_commit(
        lambda: fire_status_change_webhook(order, new_status, webhook_url)
    )

    return order


@transaction.atomic
def create_order_comment(
    order: Order,
    commented_by,
    message: str,
    comment_type: str = OrderComment.COMMENT_TYPE_GENERAL,
) -> OrderComment:
    return OrderComment.objects.create(
        order=order,
        commented_by=commented_by,
        comment_type=comment_type,
        message=message,
    )
