"""
Fiat escrow service for Indian settlement rails.
The default runtime mode is a zero-cost mock provider so the project can run without
paying for any external payment service during development. Real sandbox providers
like Razorpay can be used later without changing the core business flow.
"""
import uuid

try:
    import razorpay
except ImportError:  # pragma: no cover - optional dependency for mock mode
    razorpay = None

from app.core.config import settings

client = None
if settings.PAYMENT_PROVIDER != "mock" and razorpay is not None:
    client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))


class EscrowService:
    """Wraps milestone escrow lifecycle with a mock provider by default."""

    @staticmethod
    def _mock_response(operation: str, amount_minor: int, payment_id: str | None = None, extra: dict | None = None) -> dict:
        payload = {
            "id": payment_id or f"mock_{operation}_{uuid.uuid4().hex[:12]}",
            "status": "mocked",
            "amount": amount_minor,
            "currency": settings.PAYMENT_CURRENCY,
            "provider": "mock",
            "notes": extra or {},
        }
        return payload

    @staticmethod
    def deposit_to_vault(amount_minor: int, client_payment_method_id: str,
                        idempotency_key: str | None = None) -> dict:
        if settings.PAYMENT_PROVIDER == "mock":
            return EscrowService._mock_response(
                "deposit",
                amount_minor,
                extra={"flow": "smartescrow_milestone_deposit", "idempotency_key": idempotency_key or str(uuid.uuid4()), "method": client_payment_method_id},
            )
        if client is None:
            raise RuntimeError("Payment provider client is not configured. Set PAYMENT_PROVIDER or external sandbox keys.")
        params = {
            "amount": amount_minor,
            "currency": settings.PAYMENT_CURRENCY,
            "payment_capture": 0,
            "notes": {"flow": "smartescrow_milestone_deposit", "idempotency_key": idempotency_key or str(uuid.uuid4())},
            "method": client_payment_method_id,
        }
        return client.order.create(params)

    @staticmethod
    def capture_payment(payment_id: str, amount_minor: int, currency: str | None = None) -> dict:
        if settings.PAYMENT_PROVIDER == "mock":
            return EscrowService._mock_response("capture", amount_minor, payment_id=payment_id)
        if client is None:
            raise RuntimeError("Payment provider client is not configured.")
        return client.payment.capture(payment_id, amount_minor, {"currency": currency or settings.PAYMENT_CURRENCY})

    @staticmethod
    def release_to_freelancer(payment_id: str, freelancer_account_id: str,
                             amount_minor: int, idempotency_key: str | None = None) -> dict:
        _ = freelancer_account_id, idempotency_key
        if settings.PAYMENT_PROVIDER == "mock":
            return EscrowService._mock_response("release", amount_minor, payment_id=payment_id)
        if client is None:
            raise RuntimeError("Payment provider client is not configured.")
        return client.payment.capture(payment_id, amount_minor, {"currency": settings.PAYMENT_CURRENCY})

    @staticmethod
    def refund_to_client(payment_id: str, amount_minor: int | None = None) -> dict:
        if settings.PAYMENT_PROVIDER == "mock":
            return EscrowService._mock_response("refund", amount_minor or 0, payment_id=payment_id)
        if client is None:
            raise RuntimeError("Payment provider client is not configured.")
        payload = {} if amount_minor is None else {"amount": amount_minor}
        return client.payment.refund(payment_id, payload)

    @classmethod
    def split_funds(cls, payment_id: str, freelancer_account_id: str,
                    total_amount_minor: int, client_award_pct: float) -> dict:
        client_minor = round(total_amount_minor * (client_award_pct / 100))
        freelancer_minor = total_amount_minor - client_minor
        refund = cls.refund_to_client(payment_id, client_minor)
        return {
            "refund": refund,
            "freelancer_minor": freelancer_minor,
            "client_minor": client_minor,
            "freelancer_account_id": freelancer_account_id,
        }

    @staticmethod
    def lock_integrity_stake(payment_method_id: str,
                             amount_minor: int = settings.INTEGRITY_STAKE_INR_PAISA) -> dict:
        if settings.PAYMENT_PROVIDER == "mock":
            return EscrowService._mock_response(
                "stake_lock",
                amount_minor,
                extra={"flow": "smartescrow_integrity_stake", "method": payment_method_id},
            )
        if client is None:
            raise RuntimeError("Payment provider client is not configured.")
        params = {
            "amount": amount_minor,
            "currency": settings.PAYMENT_CURRENCY,
            "payment_capture": 0,
            "method": payment_method_id,
            "notes": {"flow": "smartescrow_integrity_stake"},
        }
        return client.order.create(params)

    @staticmethod
    def release_integrity_stake(payment_id: str) -> dict:
        if settings.PAYMENT_PROVIDER == "mock":
            return EscrowService._mock_response("stake_release", 0, payment_id=payment_id)
        if client is None:
            raise RuntimeError("Payment provider client is not configured.")
        return client.payment.fetch(payment_id)

    @staticmethod
    def slash_integrity_stake(payment_id: str, slash_amount_minor: int) -> dict:
        if settings.PAYMENT_PROVIDER == "mock":
            return EscrowService._mock_response("stake_slash", slash_amount_minor, payment_id=payment_id)
        if client is None:
            raise RuntimeError("Payment provider client is not configured.")
        return client.payment.refund(payment_id, {"amount": slash_amount_minor})
