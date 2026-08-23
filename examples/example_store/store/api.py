from fastapi import APIRouter

from store.checkout import CheckoutService

router = APIRouter()


@router.post("/checkout")
def checkout_endpoint(amount: int):
    checkout_service = CheckoutService()
    return checkout_service.checkout(amount)
