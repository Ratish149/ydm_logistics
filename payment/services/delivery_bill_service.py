from django.db import transaction

from payment.models import DeliveryBillPayment


@transaction.atomic
def create_delivery_bill_service(
    user, created_by, orders=None, delivery_amount=0.00, status="Pending"
) -> DeliveryBillPayment:
    """
    Service to create a DeliveryBillPayment and associate multiple Orders.
    """
    delivery_bill = DeliveryBillPayment.objects.create(
        user=user,
        created_by=created_by,
        delivery_amount=delivery_amount,
        status=status,
    )

    if orders:
        delivery_bill.orders.set(orders)

    return delivery_bill
