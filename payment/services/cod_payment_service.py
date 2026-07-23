from django.db import transaction

from payment.models import CodPayment


@transaction.atomic
def create_cod_payment_service(
    user, created_by, orders=None, delivery_amount=0.00, total_amount=0.00, status="Pending"
) -> CodPayment:
    """
    Service to create a CodPayment and associate multiple Orders.
    """
    cod_payment = CodPayment.objects.create(
        user=user,
        created_by=created_by,
        delivery_amount=delivery_amount,
        total_amount=total_amount,
        status=status,
    )

    if orders:
        cod_payment.orders.set(orders)

    return cod_payment
