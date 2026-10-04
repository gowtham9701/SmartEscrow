# Getting & Setting SMTP Credentials (Real Email OTP)

This guide shows exactly **how to obtain** free SMTP credentials and **where to
put them** so SmartEscrow sends real verification emails. Pick ONE provider.

The code that consumes these is already written:
- Sender: [`backend/app/marketplace/notifications.py`](../backend/app/marketplace/notifications.py)
- Config: [`backend/app/core/config.py`](../backend/app/core/config.py) (`SMTP_*`, `OTP_DELIVERY`)
- Wired into registration: [`backend/app/marketplace/store.py`](../backend/app/marketplace/store.py) → `start_registration()` / `resend_registration_otp()`

Once credentials are set, `OTP_DELIVERY=auto` switches delivery from on-screen
(demo) to real email automatically.

---

## Option A — Gmail App Password (fastest, free)

> Requires a Google account with 2-Step Verification ON. An "App Password" is a
> 16-character password that lets an app send mail through your Gmail SMTP
> without exposing your real password.

1. Go to <https://myaccount.google.com/security>.
2. Turn on **2-Step Verification** (if not already).
3. Open **App passwords**: <https://myaccount.google.com/apppasswords>
   (or search "App passwords" in your Google Account).
4. App name: type `SmartEscrow` → click **Create**.
5. Google shows a 16-character password like `abcd efgh ijkl mnop`.
   Copy it and **remove the spaces** → `abcdefghijklmnop`.
6. Use these values:

```bash
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=youraddress@gmail.com
SMTP_PASSWORD=abcdefghijklmnop        # the 16-char app password, no spaces
SMTP_FROM=SmartEscrow <youraddress@gmail.com>
SMTP_USE_TLS=true
OTP_DELIVERY=auto
```

Daily limit on free Gmail is ~500 emails — plenty for a demo/MVP.

---

## Option B — Brevo (Sendinblue) — 300 emails/day free

1. Create a free account at <https://www.brevo.com>.
2. Go to **SMTP & API** → **SMTP** tab (<https://app.brevo.com/settings/keys/smtp>).
3. Brevo shows your SMTP server, port, login, and lets you **Generate a new
   SMTP key** (this is the password).
4. Use these values:

```bash
SMTP_HOST=smtp-relay.brevo.com
SMTP_PORT=587
SMTP_USER=your-brevo-login@smtp-brevo.com   # shown on the SMTP page
SMTP_PASSWORD=your-generated-smtp-key
SMTP_FROM=SmartEscrow <you@yourdomain.com>  # verify a sender in Brevo first
SMTP_USE_TLS=true
OTP_DELIVERY=auto
```

---

## Option C — Resend — 3,000 emails/month free

1. Create a free account at <https://resend.com>.
2. Add & verify a domain (or use their test/onboarding sender for trials).
3. Go to **API Keys** → create a key. Resend's SMTP uses:

```bash
SMTP_HOST=smtp.resend.com
SMTP_PORT=587
SMTP_USER=resend
SMTP_PASSWORD=re_your_api_key
SMTP_FROM=SmartEscrow <onboarding@resend.dev>   # or your verified domain
SMTP_USE_TLS=true
OTP_DELIVERY=auto
```

---

## Where to put the credentials

### Local development
Create `backend/.env` (copy from [`backend/.env.example`](../backend/.env.example))
and paste the SMTP block. Restart the backend:

```bash
cd backend
uvicorn app.main:app --reload --port 8000
```

`config.py` loads `.env` automatically (via `pydantic-settings`).

### Production on Render
1. Open your Render Web Service → **Environment** tab.
2. Add each variable as a key/value (`SMTP_HOST`, `SMTP_PORT`, `SMTP_USER`,
   `SMTP_PASSWORD`, `SMTP_FROM`, `SMTP_USE_TLS`, `OTP_DELIVERY`).
3. Click **Save Changes** — Render redeploys with the new env.

> Never commit real credentials. `.env` is gitignored; only `.env.example`
> (with placeholders) is tracked.

---

## Test it

1. Restart the backend with the SMTP vars set.
2. Register a new user in the UI.
3. The verify screen now shows **"Codes sent to your email"** (not the numbers),
   and the email arrives with both the email + mobile codes.

If sending fails (bad credentials, network), the app **falls back to demo mode**
automatically so no one is ever blocked — check the backend logs for the SMTP
error, fix the variable, and redeploy.

---

## Why not SMS?

Real SMS requires a paid gateway (Twilio, Vonage, MSG91…) — there is no reliable
free SMS tier. **Verification is therefore email-only.** The mobile number is
still collected for contact, but no SMS code is sent (no cost).

## If SMTP ports are blocked (use Resend HTTP API)

Some networks/hosts block outbound SMTP (ports 587/465). In that case use
**Resend**, which sends over HTTPS (443) and works everywhere — free 3,000/mo:

1. Sign up at <https://resend.com> and create an API key.
2. Set `RESEND_API_KEY=re_your_key` (and `SMTP_FROM=SmartEscrow <onboarding@resend.dev>`
   or your verified domain). No SMTP vars needed.
3. The sender in [`notifications.py`](../backend/app/marketplace/notifications.py)
   automatically prefers Resend when `RESEND_API_KEY` is set.
