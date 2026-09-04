# Implementation Plan: Clerk Auth & Stripe Billing in AutoML

This plan outlines the step-by-step phases to integrate Clerk Authentication and Stripe Subscription Billing into the **AutoML** platform.

---

## 1. User Review Required
* **Environment Variables:** You must configure these keys in your deployment dashboards:
  * **Vercel (Frontend):**
    * `NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY`
    * `CLERK_SECRET_KEY`
  * **Render (Backend):**
    * `CLERK_SECRET_KEY`
    * `STRIPE_SECRET_KEY` (Used in backend or linked in Clerk integrations)
* **JWT Decoding Mechanism:** The backend will verify Clerk's JWT tokens offline using Clerk's JSON Web Key Set (JWKS) to ensure fast, secure authorization.

---

## 2. Proposed Changes

### [Component 1] Database Schema Update (SQLite & Neon PostgreSQL)
#### [NEW] [db/migrate_auth.py](file:///c:/Users/KIIT/Desktop/AutoML/backend/db/migrate_auth.py)
* Creates a migration script to:
  1. Add a `user_id` column to the `runs` table (VARCHAR type) to store the Clerk user ID (e.g. `user_...`).
  2. Index the `user_id` column to optimize multi-tenant query speeds.

---

### [Component 2] Next.js Frontend Authentication
#### [MODIFY] [frontend/package.json](file:///c:/Users/KIIT/Desktop/AutoML/frontend/package.json)
* Add `@clerk/nextjs` to dependencies.

#### [MODIFY] [frontend/app/layout.js](file:///c:/Users/KIIT/Desktop/AutoML/frontend/app/layout.js)
* Wrap the app layout inside `<ClerkProvider>` to supply auth context globally.

#### [NEW] [frontend/middleware.js](file:///c:/Users/KIIT/Desktop/AutoML/frontend/middleware.js)
* Set up a Clerk route guard middleware protecting all dashboard pages, automatically redirecting unauthenticated visitors to the login screen.

#### [MODIFY] [frontend/app/page.js](file:///c:/Users/KIIT/Desktop/AutoML/frontend/app/page.js)
* Add the Clerk `<UserButton />` in the top header row.
* Append the Clerk authorization token to headers in Vercel API calls:
  `Authorization: Bearer <clerk_jwt>`

---

### [Component 3] FastAPI Backend Verification
#### [MODIFY] [backend/requirements.txt](file:///c:/Users/KIIT/Desktop/AutoML/backend/requirements.txt)
* Append:
  ```text
  PyJWT==2.10.1
  cryptography==44.0.0
  ```

#### [NEW] [backend/auth.py](file:///c:/Users/KIIT/Desktop/AutoML/backend/auth.py)
* Implements the `get_current_user` guard:
  - Fetches Clerk's JWKS public keys.
  - Decodes and verifies incoming Bearer JWT tokens.
  - Returns `user_id` (extracted from the token's `sub` claim).

#### [MODIFY] [backend/main.py](file:///c:/Users/KIIT/Desktop/AutoML/backend/main.py)
* Add `user_id` verification requirements to all routes (`/api/upload`, `/api/runs`, `/api/runs/{run_id}/trigger`, `/api/runs/{run_id}/status`).
* Scope database queries to the authenticated user's ID:
  `db.query(AutoMLRun).filter(AutoMLRun.user_id == current_user_id)`

---

## 3. Verification Plan

### Manual Verification
- Access the homepage. Verify it redirects you to the Clerk Login page.
- Log in and verify that the Header displays your profile picture button.
- Create an AutoML run. Verify in the database that the run record has your specific Clerk `user_id` attached.
- Log out, sign in with a different account, and verify that you cannot see the runs created by the first account.
