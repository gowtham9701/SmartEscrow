"""
Fiat escrow service for Indian settlement rails.
Uses Razorpay for creating orders, capturing payments, and issuing refunds.
The code stays provider-neutral in naming while using Razorpay as the implementation.
"""
import uuid

import razorpay

from app.core.config import settings

client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))


class EscrowService:
    """Wraps Razorpay payment flows for milestone escrow lifecycle."""

    @staticmethod
    def deposit_to_vault(amount_minor: int, client_payment_method_id: str,
                        idempotency_key: str | None = None) -> dict:
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
        return client.payment.capture(payment_id, amount_minor, {"currency": currency or settings.PAYMENT_CURRENCY})

    @staticmethod
    def release_to_freelancer(payment_id: str, freelancer_account_id: str,
                             amount_minor: int, idempotency_key: str | None = None) -> dict:
        _ = freelancer_account_id, idempotency_key
        return client.payment.capture(payment_id, amount_minor, {"currency": settings.PAYMENT_CURRENCY})

    @staticmethod
    def refund_to_client(payment_id: str, amount_minor: int | None = None) -> dict:
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
        return client.payment.fetch(payment_id)

    @staticmethod
    def slash_integrity_stake(payment_id: str, slash_amount_minor: int) -> dict:
        return client.payment.refund(payment_id, {"amount": slash_amount_minor})
