# SmartEscrow — Demo Credentials & Test Data

This document lists every piece of sample data you need to run a full demo:
login accounts, employer/firm registration details, mock payment cards, and
notes on how the OTP verification works.

> All seeded accounts share the password: **`Password123!`**
>
> You can log in with either the **username** or the **email**.

---

## 1. Sample Freelancer (Job-Seeker) Accounts

These users are in **Freelancer** mode by default, already have resumes on file,
and appear in **Find Talent**. Use the header toggle to switch any of them to
**Employer** mode (which will prompt for firm verification).

| # | Name | Username | Email | Skills (sample) | Rate |
|---|------|----------|-------|-----------------|------|
| 1 | Ava Chen | `ava.chen` | ava.chen@smartescrow.io | Python, FastAPI, React, AWS | $75/hr |
| 2 | Marcus Bauer | `marcus.bauer` | marcus.bauer@smartescrow.io | Go, Rust, gRPC, Kubernetes | $72/hr |
| 3 | Diego Morales | `diego.m` | diego.m@smartescrow.io | Python, PyTorch, LLM, NLP | $95/hr |
| 4 | Priya Raman | `priya.r` | priya.r@smartescrow.io | Figma, UI/UX, React | $55/hr |
| 5 | Arjun Nair | `arjun.nair` | arjun.nair@smartescrow.io | Java, Spring, PostgreSQL | $62/hr |
| 6 | Ananya Reddy | `ananya.reddy` | ananya.reddy@smartescrow.io | React, Next.js, TypeScript | $55/hr |
| 7 | Meera Iyer | `meera.iyer` | meera.iyer@smartescrow.io | Python, ML, Data, SQL | $60/hr |
| 8 | Lena Kowalski | `lena.k` | lena.k@smartescrow.io | Security, Pentest, Crypto | $100/hr |

(Other seeded freelancers: `yuki.tanaka`, `sofia.rossi`, `aisha.khan`,
`noah.w`, `sam.okafor`, `tomas.silva`, `hannah.lee`, `rohit.sharma`.)

---

## 2. Sample Employer (Client / Organization) Accounts

These accounts are **verified firms** in **Employer** mode — they can post
jobs, review applicants, hire, and fund escrow. Each has a funded wallet.

| # | Contact | Username | Email | Company | Industry |
|---|---------|----------|-------|---------|----------|
| 1 | Jordan Blake | `client` | client@apexlabs.io | Apex Labs | Financial Technology |
| 2 | Mara Lindqvist | `hiring` | hiring@novaworks.io | NovaWorks | SaaS / Enterprise |
| 3 | Ethan Park | `talent` | talent@northlane.com | Northlane GCC | Global Capability Center |
| 4 | Dr. Amara Osei | `jobs` | jobs@helixhealth.io | Helix Health | HealthTech |
| 5 | Liam Chen | `recruiting` | recruiting@vertexdyn.com | Vertex Dynamics | Enterprise / MNC |
| 6 | Kavya Menon | `careers` | careers@infytechindia.com | InfyTech India | IT Services / GCC |

---

## 3. Firm Registration Details (for the "Register Your Firm" form)

When a freelancer switches to **Employer** mode, they must verify a business.
Use any of these sample sets (demo verification is instant — the registration
number just needs to be 4+ characters and the work email must be valid):

**Set A**
- Company / Firm Name: `Orbit Systems Pvt Ltd`
- Business Reg. Number: `CIN-U72900KA2021PTC098765`
- Work Email: `founder@orbitsystems.io`
- Website: `https://orbitsystems.io`
- Company Size: `11-50` · Industry: `Technology`

**Set B**
- Company / Firm Name: `BlueHarbor Analytics`
- Business Reg. Number: `REG-5582194`
- Work Email: `ops@blueharbor.ai`
- Website: `https://blueharbor.ai`
- Company Size: `51-200` · Industry: `SaaS / Enterprise`

**Set C**
- Company / Firm Name: `Nimbus Digital GCC`
- Business Reg. Number: `GST-29ABCDE1234F1Z5`
- Work Email: `talent@nimbusdigital.com`
- Website: `https://nimbusdigital.com`
- Company Size: `1000+` · Industry: `Global Capability Center`

**Set D**
- Company / Firm Name: `Meridian HealthTech`
- Business Reg. Number: `REG-889900`
- Work Email: `careers@meridianhealth.io`
- Website: `https://meridianhealth.io`
- Company Size: `501-1000` · Industry: `HealthTech`

**Set E**
- Company / Firm Name: `Quanta Labs`
- Business Reg. Number: `CIN-U72200TG2020PTC140022`
- Work Email: `hello@quantalabs.dev`
- Website: `https://quantalabs.dev`
- Company Size: `11-50` · Industry: `Technology`

---

## 4. Mock Payment Cards (Wallet Top-Up / Escrow)

The payment gateway is **simulated** (no real charge). Use these test cards in
the "SmartEscrow Pay" window:

| Card Number | Brand | Result |
|-------------|-------|--------|
| `4242 4242 4242 4242` | Visa | ✅ Success |
| `4000 0565 5665 5556` | Visa | ✅ Success |
| `5555 5555 5555 4444` | Mastercard | ✅ Success |
| `5200 8282 8282 8210` | Mastercard | ✅ Success |
| `3782 822463 10005` | Amex | ✅ Success |
| `4000 0000 0000 0002` | Visa | ❌ Declined |
| `4000 0000 0000 9995` | Visa | ❌ Insufficient funds |

**Rules for all cards:**
- **Expiry:** any future date (e.g. `12 / 28`)
- **CVV:** any 3–4 digits (e.g. `123`)
- **PIN:** any 4 digits **except `0000`** (which simulates a bank decline)
- Any other **Luhn-valid** card number also succeeds.

Sample full entry: `4242 4242 4242 4242`, exp `12/28`, CVV `123`, PIN `1234`.

---

## 5. OTP Verification — How It Works

Email + mobile OTPs are used during **registration**.

- The codes are **randomly generated per request** and validated server-side
  (they are **not** static). They expire after 15 minutes.
- **Delivery mode is automatic:**
  - **Demo mode (default):** when no SMTP email provider is configured, the two
    codes are shown on the verification screen so you can continue instantly.
  - **Real email mode:** set the SMTP environment variables (see
    `docs/OTP_EMAIL_SETUP.md`) and the codes are emailed for real — the screen
    then shows "Codes sent to your email" instead of the numbers.
- **Mobile OTP:** real SMS requires a paid gateway, so the mobile code is
  delivered in the **same verification email** (there is no free SMS option).

---

## 6. Quick Demo Script

1. **Browse anonymously** — open `/jobs` and `/talent`.
2. **Log in as an employer** — `client` / `Password123!` → post a job, review
   applicants, hire, fund escrow (use a test card), release payment.
3. **Log in as a freelancer** — `ava.chen` / `Password123!` → see AI resume
   insights, apply to a matched job, log hours, withdraw earnings.
4. **Register a brand-new user** — `/register` → verify with the on-screen OTPs
   → upload a resume (PDF/DOCX/TXT) → watch AI extract skills & recommend jobs.
5. **Switch modes** — use the header **Freelancer / Employer** toggle; register a
   firm with a Set from section 3 to unlock employer rights.
6. **Toggle theme** — use the 🌙 / ☀️ button (top-right) for light/dark.
