from store.payment import PaymentService


class CheckoutService:
    def __init__(self) -> None:
        self.payment_service = PaymentService()

    def checkout(self, amount: int):
        return self.payment_service.charge(amount)
