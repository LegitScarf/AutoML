# Implementation Plan: Codebase Security Sanitization & Server Alignment

This plan outlines the end-to-end strategy to eliminate all hardcoded secrets, personal ngrok tunnels, local OS filesystem paths, and sensitive database files from the AutoML codebase before pushing to GitHub. It also defines the exact environment variable configurations required across Render, Vercel, and Hugging Face.

---

## User Review Required

> [!IMPORTANT]
> **No code modifications or git commands will be executed until you review and approve this plan.**

> [!WARNING]
> - `automl_local.db` is currently tracked in Git history. We will untrack it using `git rm --cached automl_local.db` so your local database remains on your disk but is never pushed to remote GitHub.
> - Setting your Hugging Face Space to **Private** will require setting `HF_TOKEN` in Render's environment variables dashboard; otherwise, the live deployed API will be blocked from accessing the ZeroGPU runner.

---

## Proposed Changes

```
┌──────────────────────────────────────────────────────────────────────────────────────────────────┐
│                                   SECURITY REMEDIATION SCOPE                                     │
└──────────────────────────────────────────────────────────────────────────────────────────────────┘

   LOCAL CODEBASE SANITIZATION               GIT TRACKING PROTECTION              CLOUD SERVERS SYNC
  ─────────────────────────────             ─────────────────────────            ────────────────────
  • Remove ngrok URL in app3.py             • Add *.db, *.sqlite to .gitignore   • Render: Add HF_TOKEN
  • Remove 'c:/Users/KIIT/...' paths        • Add static/bundles/ to .gitignore  • Render: Add HF_SANDBOX_URL
  • Remove 'LegitScarf/...' fallback        • Untrack automl_local.db from Git   • Vercel: Verify API URL
  • Parameterize Stripe link                • Ensure .env remains ignored        • HF: Set Space to Private
```

---

### Component 1: Git Tracking & Storage Security

#### [MODIFY] [`.gitignore`](file:///c:/Users/KIIT/Desktop/AutoML/.gitignore)
- Add explicit ignore patterns for local SQLite databases:
  ```gitignore
  # Databases & telemetry state
  *.db
  *.sqlite
  *.sqlite3
  automl_local.db
  test_blackbox.db
  ```
- Add ignore pattern for generated model export zip archives:
  ```gitignore
  # Generated model artifacts & bundles
  static/bundles/
  static/bundles/*.zip
  *.zip
  ```

#### [GIT ACTION] Untrack `automl_local.db`
- Execute: `git rm --cached automl_local.db`
- **Effect:** Removes the database file from Git staging index while keeping your existing local database intact on your computer.

---

### Component 2: Backend Orchestrator Sanitization

#### [MODIFY] [`backend/orchestrator.py`](file:///c:/Users/KIIT/Desktop/AutoML/backend/orchestrator.py)
1. **Remove Hardcoded Fallback Space Slug:**
   - Change `HF_SANDBOX_URL = os.getenv("HF_SANDBOX_URL", "LegitScarf/automl-sandbox")` to:
     ```python
     HF_SANDBOX_URL = os.getenv("HF_SANDBOX_URL")
     ```
   - Add a check at pipeline boot: if `HF_SANDBOX_URL` is missing or empty, raise a descriptive configuration error (`"HF_SANDBOX_URL is not set in environment."`).
2. **Token Sanitization Guard:**
   - Ensure placeholder tokens (e.g. `"hf_your_access_token_here"` or empty whitespace) are discarded automatically:
     ```python
     raw_token = os.getenv("HF_TOKEN", "").strip()
     HF_TOKEN = raw_token if raw_token and not raw_token.startswith("hf_your_") else None
     ```
3. **Socket Reconnection Safety:**
   - Refresh the `gradio_client.Client` connection right before dispatching the execution task (`/execute`) to eliminate socket drops caused by the 60-second idle gap while the Planner and Coder LLMs are running.

---

### Component 3: Streamlit & Python UI Sanitization

#### [MODIFY] [`app3.py`](file:///c:/Users/KIIT/Desktop/AutoML/app3.py)
1. **Remove Personal ngrok URL (Line 859):**
   - Replace `webhook_url = "https://your-ngrok-tunnel.ngrok-free.dev/webhook/trigger-automl"` with:
     ```python
     webhook_url = os.getenv("N8N_WEBHOOK_URL", "http://localhost:5678/webhook/trigger-automl")
     ```
2. **Remove Hardcoded Windows Paths with Local Username (Lines 865, 872):**
   - Replace `"c:/Users/<username>/Desktop/AutoML/uploaded_dataset.csv"` with a relative path or OS temp file (`os.path.join(tempfile.gettempdir(), "uploaded_dataset.csv")`).
   - Replace default dataset path `"c:/Users/<username>/Desktop/AutoML/sample_dataset.csv"` with `"./sample_dataset.csv"`.

#### [MODIFY] [`app.py`](file:///c:/Users/KIIT/Desktop/AutoML/app.py)
1. **Remove Hardcoded Windows Path (Line 26):**
   - Replace default dataset path `"c:/Users/KIIT/Desktop/AutoML/sample_dataset.csv"` with `"./sample_dataset.csv"`.

---

### Component 4: Frontend UI Configuration Sanitization

#### [MODIFY] [`frontend/app/page.js`](file:///c:/Users/KIIT/Desktop/AutoML/frontend/app/page.js)
1. **Parameterize Stripe Link (Line 837):**
   - Replace hardcoded `https://buy.stripe.com/test_eVaeYm2zL6gW34s3cc` with:
     ```javascript
     href={process.env.NEXT_PUBLIC_STRIPE_PAYMENT_LINK || 'https://buy.stripe.com/test_eVaeYm2zL6gW34s3cc'}
     ```
   - Allows changing or disabling checkout links via Vercel environment variables without code modification.

---

### Component 5: External Cloud Infrastructure Alignment

This phase specifies the manual configuration actions required on your cloud accounts:

```
                  ┌────────────────────────────────────────────────────────┐
                  │                 EXTERNAL CLOUD SYNC MAP                │
                  └────────────────────────────────────────────────────────┘

    HUGGING FACE SPACES                 RENDER (BACKEND)                    VERCEL (FRONTEND)
   ─────────────────────               ──────────────────                  ───────────────────
   • Space: LegitScarf/automl-sandbox  • Web Service Dashboard             • Project Settings
   • Settings -> Visibility -> Private • Environment Variables:            • Environment Variables:
   • Settings -> Access Tokens:          - HF_TOKEN = <fine-grained-token>   - NEXT_PUBLIC_API_URL = <render-url>
     Create Fine-Grained 'Read-Only'     - HF_SANDBOX_URL = <space-slug>     - NEXT_PUBLIC_CLERK_...
```

#### 1. Hugging Face Spaces:
- **Change Visibility:** Go to `https://huggingface.co/spaces/LegitScarf/automl-sandbox` $\rightarrow$ **Settings** $\rightarrow$ change visibility from **Public** to **Private**.
- **Generate Token:** In HF **Settings $\rightarrow$ Access Tokens**, create a **Fine-grained Token**:
  - Name: `automl-backend-sandbox`
  - Scope: `LegitScarf/automl-sandbox`
  - Permissions: **Read-Only** (Read access to contents and state of selected Spaces).

#### 2. Render (FastAPI Backend Gateway):
- In Render Dashboard $\rightarrow$ your FastAPI Web Service $\rightarrow$ **Environment**:
  - Add `HF_TOKEN`: `<your-new-fine-grained-token>`
  - Add `HF_SANDBOX_URL`: `LegitScarf/automl-sandbox`
  - Add `OPENAI_API_KEY`: `<your-openai-key>`
  - Add `CLERK_SECRET_KEY`: `<your-clerk-secret-key>`
  - Add `DATABASE_URL`: `<your-render-or-neon-postgres-url>`

#### 3. Vercel (Next.js 14 Frontend):
- In Vercel Dashboard $\rightarrow$ your AutoML Frontend project $\rightarrow$ **Settings $\rightarrow$ Environment Variables**:
  - `NEXT_PUBLIC_API_URL`: `https://<your-render-service>.onrender.com`
  - `NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY`: `pk_...`
  - `CLERK_SECRET_KEY`: `sk_...`
  - `NEXT_PUBLIC_STRIPE_PAYMENT_LINK`: `<your-stripe-url>`
  - ⚠️ Verify `HF_TOKEN` is **NOT** on Vercel.

---

## Verification Plan

### Automated Verification
1. **Git Tracking Check:**
   - Run `git status` to verify `automl_local.db`, `test_blackbox.db`, and `static/bundles/` are untracked and ignored.
   - Run `git ls-files automl_local.db` to verify output is empty.
2. **Secret Scan Check:**
   - Run a ripgrep scan across the repository to verify that:
     - No `ngrok-free.dev` URLs exist.
     - No `c:/Users/KIIT` paths exist in tracked code.
     - No hardcoded `LegitScarf` fallback strings remain in executable `.py` files.
3. **Automated Pytest Suite:**
   - Run `pytest tests/test_core_pipeline.py -v` to ensure local profiling and sandbox validation pass without regression.

### Manual Verification
1. Verify backend starts cleanly with local `.env` loaded:
   `python -m uvicorn backend.main:app --port 8000`
2. Test calling `/api/upload` and verifying pipeline triggers properly.
