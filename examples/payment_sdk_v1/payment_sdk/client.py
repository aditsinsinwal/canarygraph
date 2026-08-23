from enum import StrEnum


class PaymentState(StrEnum):
    APPROVED = "approved"
    DECLINED = "declined"
    PENDING = "pending"


class PaymentClient:
    def create_payment(self, amount: int) -> dict[str, object]:
        return {"amount": amount, "status": PaymentState.APPROVED}

    def capture(self, payment_id: str) -> bool:
        return bool(payment_id)

    def refund(self, payment_id: str, reason: str = "customer_request") -> bool:
        return bool(payment_id and reason)


class LegacyClient:
    def ping(self) -> bool:
        return True


def parse_webhook(payload: bytes) -> dict[str, object]:
    return {"raw": payload}
