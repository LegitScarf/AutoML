# Implementation Plan: Clerk Auth & Stripe Billing in Omega

This plan outlines the step-by-step phase integration to add authentication and billing to the Omega AutoML platform.

---

## Phase 1: Accounts & Environment Setup

1. **Clerk Dashboard:**
   - Create a Clerk account and set up a new project named `omega-auth`.
   - Retrieve API keys: `NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY` and `CLERK_SECRET_KEY`.
2. **Stripe Dashboard (Developer Mode):**
   - Retrieve API keys: `STRIPE_API_KEY` (Secret Key) and `NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY`.
   - Setup a Product (Subscription model, e.g., $10/month) and copy its `PRICE_ID`.
3. **Inject Environment Variables:**
   - Add keys to **Vercel** and **Render** environment settings.

---

## Phase 2: Database Schema Update (Neon PostgreSQL)

We will execute SQL modifications to link users and runs:

```sql
-- Create users table
CREATE TABLE users (
    id VARCHAR(100) PRIMARY KEY, -- Maps to Clerk User ID (user_...)
    email VARCHAR(255) UNIQUE NOT NULL,
    tier VARCHAR(50) DEFAULT 'free', -- 'free' or 'premium'
    stripe_customer_id VARCHAR(255) UNIQUE,
    stripe_subscription_id VARCHAR(255) UNIQUE,
    subscription_status VARCHAR(50),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Alter runs table to link to users
ALTER TABLE runs ADD COLUMN user_id VARCHAR(100);
ALTER TABLE runs ADD CONSTRAINT fk_user FOREIGN KEY (user_id) REFERENCES users(id);
```

---

## Phase 3: Frontend Auth Integration (Clerk)

1. **Install SDK:**
   ```bash
   cd frontend
   npm install @clerk/nextjs
   ```
2. **Configure Provider:**
   Wrap `frontend/app/layout.js` inside `<ClerkProvider>` to enable application-wide auth context.
3. **Route Protection:**
   Create a middleware file `frontend/middleware.js` to protect dashboard routes (`/`) from unauthenticated users, redirecting them to Clerk's hosted sign-in page.
4. **Header Profile Component:**
   Update `brand-row` in `frontend/app/page.js` to render Clerk's `<UserButton />` containing profile updates, sign-out actions, and user info.

---

## Phase 4: Backend Auth Guard (FastAPI JWT Verification)

1. **Install JWT Packages:**
   ```bash
   cd backend
   pip install PyJWT cryptography
   ```
2. **Implement Token Decoder (`backend/auth.py`):**
   - Fetch JWKS keys on startup from Clerk's JSON keys endpoint.
   - Decode Bearer Tokens sent in headers, extracting the user ID.
3. **Protect Endpoints:**
   Update FastAPI routers in `backend/main.py` to require the user ID dependency:
   ```python
   # Example endpoint guard
   @app.post("/api/upload")
   def upload(file: UploadFile, current_user = Depends(get_current_user)):
       # Access user_id via current_user.id
   ```

---

## Phase 5: Stripe Integration & Checkout

1. **Install SDK:**
   ```bash
   cd backend
   pip install stripe
   ```
2. **Stripe Router (`backend/payments.py`):**
   - Endpoint `POST /api/payments/checkout`: Generates a Stripe checkout session mapping the current user's ID as metadata and redirects them to the checkout page.
3. **Stripe Webhook (`POST /api/payments/webhook`):**
   - Reads the raw request body and verifies Stripe signature (`STRIPE_WEBHOOK_SECRET`).
   - Listens to `checkout.session.completed` and `customer.subscription.updated` to update the corresponding Neon DB `users` status.

---

## Phase 6: Verification & Testing Checklist

- [ ] **Auth Check:** Accessing `/` redirects to the login screen.
- [ ] **JWT Ingestion:** Frontend API calls include the `Authorization` header containing the JWT token.
- [ ] **Multi-Tenancy Check:** Logging in with Account A does not list runs created by Account B.
- [ ] **Stripe Check:** Triggering checkout launches the Stripe dashboard; completing test card transactions updates the Neon database user status to "premium".
