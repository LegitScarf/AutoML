# Deep Architectural Study: Payment Gateway & Free Limit Bypass in AutoML

**Date:** September 5, 2026  
**Subject:** Architectural Analysis of Stripe/Clerk Integration & Zero-Friction Unlimited Run Bypass  
**Status:** COMPLETED  

---

## 1. Architectural Verdict: Direct Stripe vs. Stripe via Clerk

> **Verdict:** The payment gateway in AutoML is implemented as **"Stripe via Clerk"** (specifically: **Hosted Stripe Payment Links + Clerk JWT Metadata Gating**), **NOT** via a direct backend Stripe SDK.

### Forensic Evidence from the Codebase & Study References

| Layer | Implementation in Codebase | Reference in `/study` |
| :--- | :--- | :--- |
| **Frontend UI** | Static Stripe Payment Link button: <br>`href={process.env.NEXT_PUBLIC_STRIPE_PAYMENT_LINK || "https://buy.stripe.com/test_..."}` in `frontend/app/page.js:877`. | Designed in `study/Public Landing Page, Free Trial Limits & Upgrade Popup.md`. |
| **Backend Auth** | Reads `tier` directly from the **Clerk JWT** payload claim: <br>`tier = payload.get("public_metadata", {}).get("tier", "free")` in `backend/auth.py:91`. | Outlined in `study/Clerk Auth & Stripe Billing in AutoML.md`. |
| **Database** | **No** `users` or `subscriptions` tables exist in `backend/models.py`. The only table is `runs`. | Earlier design in `study/omega_auth_payments_architecture.md` proposed `stripe_customer_id` columns, but was **never implemented**. |
| **Stripe SDK** | Neither `stripe` (Python) nor `@stripe/stripe-js` (Node) exists in `backend/requirements.txt` or `frontend/package.json`. | No webhook handlers (`/api/payments/webhook`) or checkout session creators exist. |

### Current Architecture Flow:
```
  [ Next.js Frontend ] ──(Upload 3rd Run)──► [ FastAPI /api/upload ]
          │                                         │
          │                                         ▼
          │                             [ Check DB run_count >= 2 ]
          │                                   AND tier != "premium"
          │                                         │
          │◄──── HTTP 403 TRIAL_LIMIT_EXCEEDED ─────┘
          ▼
  [ showUpgradeModal(true) ]
          │
          ▼
  [ Glassmorphic Modal with Hosted Stripe Link (buy.stripe.com/...) ]
```

---

## 2. Why Switching Off Billing is 100% Safe

1. **Zero Database Migrations Required**: The database only tracks `runs`, which already supports unlimited records per user. No schema modifications or migrations are needed.
2. **Zero External API Disruption**: We do not need to alter any Stripe webhooks or Clerk dashboard settings.
3. **Core ML Pipeline Unaffected**: The pipeline steps (Pandas Profiler ➔ Planner Agent ➔ Coder Agent ➔ Hugging Face ZeroGPU Sandbox ➔ Model Bundle Download) do not depend on the tier check; they only depend on the run being created in the database.

---

## 3. The Simplest Approach: Feature-Flagged Bypass

The cleanest and most production-ready pattern is introducing a single toggle (`ENABLE_TRIAL_LIMITS`) in the backend, defaulting to `False`.

### Exactly What Changes:

#### 1. Backend: Guard the Trial Limit in `backend/main.py` (lines 88-93)
```python
# Check feature flag (Default: False -> Unlimited free runs, payment gateway disabled)
ENABLE_TRIAL_LIMITS = os.getenv("ENABLE_TRIAL_LIMITS", "false").lower() == "true"

if ENABLE_TRIAL_LIMITS and user_tier != "premium":
    run_count = db.query(AutoMLRun).filter(AutoMLRun.user_id == current_user_id).count()
    if run_count >= 2:
        raise HTTPException(status_code=403, detail="TRIAL_LIMIT_EXCEEDED")
```

#### 2. Backend: Default User Tier to `"premium"` in `backend/auth.py` (line 91)
```python
# Default to "premium" while billing is switched off
ENABLE_TRIAL_LIMITS = os.getenv("ENABLE_TRIAL_LIMITS", "false").lower() == "true"
tier = payload.get("public_metadata", {}).get("tier", "premium" if not ENABLE_TRIAL_LIMITS else "free")
```

---

## 4. Operational Results After Bypass

1. **Unlimited Runs**: Every authenticated user (new or existing) can upload datasets and execute unlimited AutoML runs without ever being stopped at run #2.
2. **Upgrade Popup Stays Dormant**: Because `/api/upload` never returns HTTP `403 TRIAL_LIMIT_EXCEEDED`, the frontend's `showUpgradeModal(true)` is never triggered.
3. **No Dead Stripe Links**: Users are never redirected to Stripe checkout links or asked for payment details.
4. **Seamless Future Reversal**: When you are ready to monetize later, you simply add `ENABLE_TRIAL_LIMITS=true` to your Render environment variables—without needing to rewrite code or re-deploy.
