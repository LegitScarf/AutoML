# Architectural Study: Clerk & Stripe Integration in Omega

This study details the architectural design to introduce user authentication (via Clerk) and subscription payments (via Stripe) into the current **Omega** (AutoML Platform) stack.

---

## 1. Current vs. Proposed Stack

| Component | Current Stack | Proposed SaaS Stack |
| :--- | :--- | :--- |
| **Frontend** | Next.js (relative URLs, stateless UI) | Next.js + `@clerk/nextjs` (authenticated routes, subscription dashboard) |
| **Backend API** | FastAPI (unauthenticated public routes) | FastAPI + PyJWT/Cryptography (bearer token parsing, user validation) |
| **Database** | Neon PostgreSQL (`runs` table only) | Neon PostgreSQL (`runs` + new `users` & `subscriptions` tables) |
| **Billing Engine**| None | Stripe Node/Python SDK + Stripe hosted webhooks |

---

## 2. Authentication Architecture (Clerk)

Clerk provides complete, secure authentication out-of-the-box. We will use a **JWT-verification** workflow to secure backend API requests without coupling Render directly to Clerk's servers on every request.

```
  [ Next.js Frontend ]
         │  1. User logs in via Clerk UI
         ▼
    (Clerk Auth Session) ──► Generates JWT (Short-lived token containing user_id)
         │
         │  2. Calls API with Header: "Authorization: Bearer <clerk_jwt>"
         ▼
  [ FastAPI Backend ]
         │  3. Retrieves Clerk's Public JSON Web Key Sets (JWKS) to verify JWT offline
         ├─► Valid JWT? Yes ──► Extracts Clerk User ID (sub claim)
         ▼
  [ Neon PostgreSQL ]
            4. Creates/Fetches User Record & associates run logs to user_id
```

### Backend Middleware Validation:
FastAPI will parse the token header. We check:
1. Token expiration (`exp`).
2. Signature validity against Clerk’s JWKS URL: `https://clerk.your-domain.com/.well-known/jwks.json`.
3. Target audience matching Clerk Application IDs.

---

## 3. Subscription & Billing Architecture (Stripe)

We will implement a **Usage-based / Subscription model** (e.g. Free Tier: 3 runs/month, Premium Tier: Unlimited runs, GPU access, PDF reports).

```
  [ Frontend UI ] ──────► 1. Click "Upgrade to Premium" ───► [ FastAPI Backend ]
        ▲                                                          │
        │ 3. Redirects to Stripe                                    ▼ 2. Create Checkout Session
        └───────────────── [ Stripe Checkout Page ] ◄──────────────┘
                                  │
                                  │ 4. Payment Succeeds
                                  ▼
                            [ Stripe API ]
                                  │
                                  ▼ 5. Sends secure webhook ("checkout.session.completed")
                           [ FastAPI Webhook ]
                                  │
                                  ▼ 6. Verify signature & update Neon DB
                           [ Neon Database ] ◄─── (User marked as PREMIUM)
```

### Data Modeling:
We will add a `users` table:
* `id` (VARCHAR - Maps to Clerk's User ID `user_...`)
* `email` (VARCHAR)
* `tier` (VARCHAR: `free`, `premium`)
* `stripe_customer_id` (VARCHAR)
* `stripe_subscription_id` (VARCHAR)
* `subscription_status` (VARCHAR)

---

## 4. Key Security Considerations
1. **Webhook Signature Verification:** The Stripe webhook route (`/api/payments/webhook`) must verify incoming payloads using the Stripe Webhook Secret (`STRIPE_WEBHOOK_SECRET`) to prevent spoofing.
2. **Metadata Association:** When creating the Stripe checkout session, we must embed the Clerk `user_id` as metadata:
   `metadata={"user_id": clerk_user_id}`.
   This guarantees that when Stripe sends the success webhook, we know exactly which user account in our database to upgrade.
3. **Database Constraints:** All database queries in the `runs` table will filter by `user_id = current_user.id` to prevent cross-user data leakage.
