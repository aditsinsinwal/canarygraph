from enum import StrEnum


class PaymentState(StrEnum):
    APPROVED = "approved"
    DECLINED = "declined"


class PaymentClient:
    def create_payment(self, amount_cents: int, currency: str) -> dict[str, object]:
        return {"amount_cents": amount_cents, "currency": currency, "status": "approved"}

    def authorize(self, payment_id: str) -> bool:
        return bool(payment_id)

    def refund(self, payment_id: str, *, reason: str) -> bool:
        return bool(payment_id and reason)
