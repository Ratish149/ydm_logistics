from decimal import Decimal

from account.models import CustomUser
from rider.models import RiderPayout


def create_rider_payout(
    rider: CustomUser, amount: Decimal, remarks: str = ""
) -> RiderPayout:
    """
    Registers a new Rider Payout transaction.
    """
    return RiderPayout.objects.create(rider=rider, amount=amount, remarks=remarks)
