from payment_sdk import PaymentClient as Client


class PaymentService:
    def __init__(self) -> None:
        self.client = Client()

    def charge(self, amount: int):
        return self.client.create_payment(amount)

    def capture(self, payment_id: str):
        return self.client.capture(payment_id)

    def refund(self, payment_id: str):
        return self.client.refund(payment_id, "duplicate")
