# Implementation Plan: Disabling Payment Gateway & Removing Free Limits

This plan outlines the minimal, non-destructive, and reversible steps to completely disable the Stripe payment gateway and lift the 2-run trial limit in **AutoML**, allowing all authenticated users to execute unlimited runs without triggering upgrade modals.

---

## 1. Architectural Highlights

- **Zero Database Migrations:** No schema updates are needed. The database already stores unlimited runs per `user_id`.
- **Zero Frontend Breaking Changes:** The frontend modal is strictly triggered by HTTP `403 TRIAL_LIMIT_EXCEEDED`. Once the backend stops returning this 403 status, the modal never appears.
- **Future-Proof Reversibility:** By introducing the `ENABLE_TRIAL_LIMITS` flag (defaulting to `False`), you can re-enable billing in the future simply by adding `ENABLE_TRIAL_LIMITS=true` to your Render environment variables without touching any code.

---

## 2. Proposed Changes

### Backend Authentication & API Layer

#### [MODIFY] `backend/main.py`
- In `/api/upload`, wrap the 2-run limit check with `ENABLE_TRIAL_LIMITS = os.getenv("ENABLE_TRIAL_LIMITS", "false").lower() == "true"`.
- When `ENABLE_TRIAL_LIMITS` is `False` (default), skip the `run_count >= 2` database check entirely.
- Ensure `/api/upload` never emits HTTP 403 `TRIAL_LIMIT_EXCEEDED`.

```python
# Check feature flag (Default: False -> Unlimited free runs, payment gateway disabled)
ENABLE_TRIAL_LIMITS = os.getenv("ENABLE_TRIAL_LIMITS", "false").lower() == "true"

# Enforce 2-run free trial limit only if feature flag is active
if ENABLE_TRIAL_LIMITS and user_tier != "premium":
    run_count = db.query(AutoMLRun).filter(AutoMLRun.user_id == current_user_id).count()
    if run_count >= 2:
        raise HTTPException(status_code=403, detail="TRIAL_LIMIT_EXCEEDED")
```

---

#### [MODIFY] `backend/auth.py`
- In `get_current_user`, default the user's tier claim to `"premium"` when `ENABLE_TRIAL_LIMITS` is disabled, and to `"free"` if billing is active:

```python
# Extract custom metadata tier synchronized from Stripe (defaulting to 'premium' when billing is disabled)
ENABLE_TRIAL_LIMITS = os.getenv("ENABLE_TRIAL_LIMITS", "false").lower() == "true"
tier = payload.get("public_metadata", {}).get("tier", "premium" if not ENABLE_TRIAL_LIMITS else "free")
```

---

## 3. Verification Plan

### Automated Tests
1. **Core Pipeline Unit Tests:**
   ```powershell
   .\.venv\Scripts\python.exe -m pytest tests/test_core_pipeline.py -v
   ```
2. **Feature Flag & Trial Bypass Simulation:**
   - Verify that with `ENABLE_TRIAL_LIMITS=false`, any user can upload unlimited runs.
   - Verify that with `ENABLE_TRIAL_LIMITS=true`, the 2-run ceiling functions as expected.

### Manual Verification
1. Verify `backend/main.py` and `backend/auth.py` compile cleanly.
2. Commit and push to GitHub branch `prod`.
3. Verify on live deployment that consecutive runs execute without encountering the upgrade popup.
