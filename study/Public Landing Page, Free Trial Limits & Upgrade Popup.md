# Implementation Plan: Public Landing Page, Free Trial Limits & Upgrade Popup

This plan details the changes to make the AutoML landing page public, check user authentication on interaction, enforce a 2-run free trial limit on the backend, and show an upgrade modal when the limit is exceeded.

---

## 1. User Review Required
* **Public Route Access:** We will remove the root route (`/`) from Next.js middleware protection. Anyone can load and explore the page.
* **Authentication Check Trigger:** When an anonymous user attempts to upload/drop a dataset or click "Run", they will be prompted to sign in via Clerk.
* **Upgrade Checkout Link:** The upgrade popup will include a button to redirect to your Stripe Checkout/Billing URL.

---

## 2. Proposed Changes

### [Component 1] Next.js Route Guard Bypass
#### [MODIFY] [frontend/middleware.js](file:///c:/Users/KIIT/Desktop/AutoML/frontend/middleware.js)
* Update `clerkMiddleware` to mark the root path `/` as a public route.
* Remove `auth().protect()` on `/`.

---

### [Component 2] Frontend Auth Checks & Upgrade Modal
#### [MODIFY] [frontend/app/page.js](file:///c:/Users/KIIT/Desktop/AutoML/frontend/app/page.js)
* **Auth Guard on Interaction:**
  - Wrap the file upload handler (`handleFileChange`, `onDragOver`, etc.) and the "Run pipeline" button handler.
  - If Clerk's `userId` is null, interrupt the event and redirect the user to Clerk's hosted sign-in screen:
    ```javascript
    import { useClerk } from '@clerk/nextjs';
    const { redirectToSignIn } = useClerk();
    if (!userId) {
      redirectToSignIn();
      return;
    }
    ```
* **Upgrade Popup Modal [NEW UI]:**
  - Add a state hook `const [showUpgradeModal, setShowUpgradeModal] = useState(false);`.
  - Design a glassmorphic premium overlay modal prompting the user to upgrade to AutoML Premium because they have exhausted their 2 free trials.
  - Include an **"Upgrade to Premium ($10/mo)"** checkout link button.
* **Intercept Trial Limitations:**
  - If `/api/upload` returns a `403` status with the error code `"TRIAL_LIMIT_EXCEEDED"`, set `showUpgradeModal(true)`.

---

### [Component 3] Backend Trial & Subscription Guard
#### [MODIFY] [backend/auth.py](file:///c:/Users/KIIT/Desktop/AutoML/backend/auth.py)
* Update `get_current_user_id` or implement a new verification wrapper that extracts the user's `tier` from Clerk's JWT claims (`payload.get("public_metadata", {}).get("tier", "free")`).

#### [MODIFY] [backend/main.py](file:///c:/Users/KIIT/Desktop/AutoML/backend/main.py)
* Inside `/api/upload`, add a trial check:
  - Query the database to count existing runs for the current `user_id`:
    `run_count = db.query(AutoMLRun).filter(AutoMLRun.user_id == current_user_id).count()`
  - If `run_count >= 2` AND `user_tier != "premium"`:
    - Raise `HTTPException(status_code=403, detail="TRIAL_LIMIT_EXCEEDED")`.

---

## 3. Verification Plan

### Manual Verification
- Access the landing page in an Incognito window. Verify it loads the full UI without redirecting to login.
- Drag a CSV file into the upload box. Verify you are redirected to Clerk's login.
- Sign in with a new test account. 
- Run 2 complete AutoML pipelines (which should succeed).
- Try to trigger a 3rd AutoML run. Verify that:
  - The backend returns a `433` / `403` trial limit error.
  - The Next.js frontend displays the premium upgrade popup modal.
