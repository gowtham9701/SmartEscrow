"""
Email OTP delivery for SmartEscrow (email-only, free).

Two free delivery backends are supported — the first one configured wins:

  1. Resend HTTP API  (RESEND_API_KEY)  — sends over HTTPS/443. Works even on
     networks that block raw SMTP ports. Free tier: 3,000 emails/month.
  2. SMTP             (SMTP_* vars)      — Gmail App Password, Brevo, etc.

If neither is configured (or a send fails) the app falls back to "demo" mode and
returns the code so on-screen verification still works.

There is intentionally NO SMS: real SMS costs money, so verification is
email-only. The mobile number is still collected for contact, but not verified.
"""
from __future__ import annotations

import json
import logging
import smtplib
import ssl
import urllib.request

from app.core.config import settings

logger = logging.getLogger("smartescrow.otp")


def resend_configured() -> bool:
    return bool(getattr(settings, "RESEND_API_KEY", ""))


def smtp_configured() -> bool:
    return bool(settings.SMTP_HOST and settings.SMTP_USER and settings.SMTP_PASSWORD)


def delivery_mode() -> str:
    mode = (settings.OTP_DELIVERY or "auto").lower()
    if mode == "auto":
        return "email" if (resend_configured() or smtp_configured()) else "demo"
    return mode


# --------------------------------------------------------------------------- #
# Backends
# --------------------------------------------------------------------------- #
def _send_via_resend(to_address: str, subject: str, body: str) -> None:
    from_header = settings.SMTP_FROM or "SmartEscrow <onboarding@resend.dev>"
    payload = json.dumps({
        "from": from_header,
        "to": [to_address],
        "subject": subject,
        "text": body,
    }).encode()
    req = urllib.request.Request(
        "https://api.resend.com/emails",
        data=payload,
        headers={
            "Authorization": f"Bearer {settings.RESEND_API_KEY}",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=15) as resp:
        if resp.status >= 300:
            raise RuntimeError(f"Resend API error {resp.status}")


def _send_via_smtp(to_address: str, subject: str, body: str) -> None:
    from email.message import EmailMessage

    msg = EmailMessage()
    msg["From"] = settings.SMTP_FROM
    msg["To"] = to_address
    msg["Subject"] = subject
    msg.set_content(body)

    context = ssl.create_default_context()
    with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT, timeout=15) as server:
        if settings.SMTP_USE_TLS:
            server.starttls(context=context)
        server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
        server.send_message(msg)


def _send_email(to_address: str, subject: str, body: str) -> None:
    """Send via whichever backend is configured (Resend preferred)."""
    if resend_configured():
        _send_via_resend(to_address, subject, body)
    elif smtp_configured():
        _send_via_smtp(to_address, subject, body)
    else:
        raise RuntimeError("No email backend configured")


# --------------------------------------------------------------------------- #
# Public API
# --------------------------------------------------------------------------- #
def send_registration_otp(email: str, full_name: str, code: str) -> dict:
    """
    Deliver the single email verification code.

    Returns {"delivery": "email", ...} on success, or {"delivery": "demo",
    "demo_otp": code} when email isn't configured or sending failed.
    """
    if delivery_mode() == "email":
        subject = "Your SmartEscrow verification code"
        body = (
            f"Hi {full_name or 'there'},\n\n"
            f"Welcome to SmartEscrow. Your email verification code is:\n\n"
            f"    {code}\n\n"
            f"It expires in {settings.OTP_TTL_MINUTES} minutes. "
            f"If you didn't request this, you can ignore this email.\n\n"
            f"— The SmartEscrow Team"
        )
        try:
            _send_email(email, subject, body)
            return {"delivery": "email", "sent_to": email}
        except Exception as exc:  # never block the user — fall back to demo
            logger.warning("OTP email send failed (falling back to demo): %s", exc)
            return {"delivery": "demo", "error": str(exc), "demo_otp": code}
    return {"delivery": "demo", "demo_otp": code}


def send_login_otp(email: str, full_name: str, code: str) -> dict:
    if delivery_mode() == "email":
        subject = "Your SmartEscrow login code"
        body = (
            f"Hi {full_name or 'there'},\n\n"
            f"Your SmartEscrow login verification code is: {code}\n\n"
            f"It expires in {settings.OTP_TTL_MINUTES} minutes.\n\n"
            f"— The SmartEscrow Team"
        )
        try:
            _send_email(email, subject, body)
            return {"delivery": "email", "sent_to": email}
        except Exception as exc:
            logger.warning("Login OTP email send failed (falling back to demo): %s", exc)
            return {"delivery": "demo", "error": str(exc), "demo_otp": code}
    return {"delivery": "demo", "demo_otp": code}
