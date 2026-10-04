# Enabling Real Email OTP (Zero-Cost)

SmartEscrow generates and validates OTP codes for real — the only thing that is
mocked by default is **delivery** (the codes are shown on screen). This guide
turns on **real email delivery** using a free provider. No code changes needed —
only environment variables.

## Why email (and not SMS)?

- **Email is free.** Gmail (App Password), Brevo, Resend, and MailerSend all
  offer free tiers that comfortably cover demo/MVP volumes.
- **SMS is not free.** Every real SMS gateway (Twilio, Vonage, MSG91, etc.)
  charges per message. There is no reliable free SMS tier. So the **mobile OTP
  is delivered inside the same verification email** instead.

## How delivery is decided

The backend reads `OTP_DELIVERY`:

- `auto` (default): send real email **if** SMTP is configured, otherwise demo.
- `email`: always send real email.
- `demo`: never send; return codes in the API response (on-screen).

## Environment variables

Set these on your host (Render → Environment, or a local `.env`):

```bash
# --- SMTP (example: Gmail with an App Password) ---
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=youraddress@gmail.com
SMTP_PASSWORD=your_16_char_app_password   # NOT your normal password
SMTP_FROM=SmartEscrow <youraddress@gmail.com>
SMTP_USE_TLS=true
OTP_DELIVERY=auto
OTP_TTL_MINUTES=15
```

### Getting a Gmail App Password (free)
1. Enable 2-Step Verification on your Google account.
2. Go to **Google Account → Security → App passwords**.
3. Generate a password for "Mail" and paste it into `SMTP_PASSWORD`.

### Free alternatives
- **Brevo (Sendinblue):** 300 emails/day free. Use their SMTP host/credentials.
- **Resend:** 3,000 emails/month free.
- **MailerSend:** 3,000 emails/month free.

For any of them, just plug the provider's SMTP host, port, username and
password into the variables above.

## Verifying it works

1. Set the variables and restart the backend.
2. Register a new user.
3. The verification screen will now say **"Codes sent to your email"** instead
   of showing the numbers, and the email (with both the email and mobile codes)
   will arrive in the inbox.

If sending fails for any reason, the app **gracefully falls back to demo mode**
so users are never blocked.
