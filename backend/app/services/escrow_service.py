"""
Automated USD Escrow Service (Stripe Connect Sandbox)
------------------------------------------------------
Strict fiat-native USD rails. No crypto, tokens, or stablecoins anywhere
in this module. All money values are integer cents to avoid float drift.
"""
import uuid

import stripe

from app.core.config import settings

stripe.api_key = settings.STRIPE_API_KEY


class EscrowService:
    """Wraps Stripe Connect sandbox calls for the milestone escrow lifecycle."""

    # -- a. Client funds a milestone into the holding vault -------------------
    @staticmethod
    def deposit_to_vault(amount_usd_cents: int, client_payment_method_id: str,
                          idempotency_key: str | None = None) -> stripe.PaymentIntent:
        return stripe.PaymentIntent.create(
            amount=amount_usd_cents,
            currency="usd",
            payment_method=client_payment_method_id,
            confirm=True,
            capture_method="manual",  # funds authorized & held, captured only on release
            idempotency_key=idempotency_key or str(uuid.uuid4()),
            metadata={"flow": "smartescrow_milestone_deposit"},
        )

    # -- e. Release escrowed USD to freelancer's connected bank account -------
    @staticmethod
    def release_to_freelancer(payment_intent_id: str, freelancer_stripe_account_id: str,
                               amount_usd_cents: int, idempotency_key: str | None = None) -> stripe.Transfer:
        # Capture the manually-held authorization, then transfer funds
        stripe.PaymentIntent.capture(payment_intent_id)
        return stripe.Transfer.create(
            amount=amount_usd_cents,
            currency="usd",
            destination=freelancer_stripe_account_id,
            transfer_group=payment_intent_id,
            idempotency_key=idempotency_key or str(uuid.uuid4()),
        )

    # -- Refund path (dispute resolved in client's favor) ---------------------
    @staticmethod
    def refund_to_client(payment_intent_id: str, amount_usd_cents: int | None = None) -> stripe.Refund:
        kwargs = {"payment_intent": payment_intent_id}
        if amount_usd_cents is not None:
            kwargs["amount"] = amount_usd_cents
        return stripe.Refund.create(**kwargs)

    # -- Split path (jury awards a percentage split) --------------------------
    @classmethod
    def split_funds(cls, payment_intent_id: str, freelancer_stripe_account_id: str,
                     total_amount_usd_cents: int, client_award_pct: float) -> dict:
        client_cents = round(total_amount_usd_cents * (client_award_pct / 100))
        freelancer_cents = total_amount_usd_cents - client_cents

        stripe.PaymentIntent.capture(payment_intent_id)
        transfer = None
        refund = None
        if freelancer_cents > 0:
            transfer = stripe.Transfer.create(
                amount=freelancer_cents,
                currency="usd",
                destination=freelancer_stripe_account_id,
                transfer_group=payment_intent_id,
            )
        if client_cents > 0:
            refund = stripe.Refund.create(payment_intent=payment_intent_id, amount=client_cents)
        return {"transfer": transfer, "refund": refund,
                "freelancer_cents": freelancer_cents, "client_cents": client_cents}

    # -- Fiat-Staking Integrity Model ------------------------------------------
    @staticmethod
    def lock_integrity_stake(payment_method_id: str,
                              amount_usd_cents: int = settings.INTEGRITY_STAKE_USD_CENTS) -> stripe.PaymentIntent:
        return stripe.PaymentIntent.create(
            amount=amount_usd_cents,
            currency="usd",
            payment_method=payment_method_id,
            confirm=True,
            capture_method="manual",
            metadata={"flow": "smartescrow_integrity_stake"},
        )

    @staticmethod
    def release_integrity_stake(payment_intent_id: str) -> stripe.PaymentIntent:
        return stripe.PaymentIntent.cancel(payment_intent_id)

    @staticmethod
    def slash_integrity_stake(payment_intent_id: str, slash_amount_usd_cents: int) -> stripe.PaymentIntent:
        stripe.PaymentIntent.capture(payment_intent_id, amount_to_capture=slash_amount_usd_cents)
        return stripe.PaymentIntent.retrieve(payment_intent_id)
