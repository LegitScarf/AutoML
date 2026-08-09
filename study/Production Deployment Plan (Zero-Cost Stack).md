# Production Deployment Plan (Zero-Cost Stack)

This plan details the step-by-step process to deploy your **Next.js Frontend to Vercel**, your **FastAPI Backend to Render**, and provision a **Free PostgreSQL Database on Neon/Supabase**, connecting them all to the active **Hugging Face Sandbox**.

---

## Technical Architecture Map

```
  [ Vercel UI ] (https://automl-frontend.vercel.app)
       │
       ▼ (Sends HTTP Requests)
  [ Render API ] (https://automl-backend.onrender.com)
       │
       ├─► [ PostgreSQL DB ] (Neon / Supabase Free Tier)
       │
       └─► [ Hugging Face Sandbox ] (https://huggingface.co/spaces/LegitScarf/automl-sandbox)
```

---

## Step 1: Provision the Free Serverless PostgreSQL Database

We need a persistent cloud database to store run metadata, status states, and console logs.

### Neon DB Setup (Recommended - Quickest Setup)
1. Go to [neon.tech](https://neon.tech/) and sign up for a free tier account (no credit card required).
2. Create a new project named `automl-prod`.
3. Select **PostgreSQL 16** (default) and your preferred region (choose the one closest to your Render location, e.g., US East).
4. Save the connection string generated for you. It will look like:
   `postgresql://owner:password@ep-cool-snowflake-1234.us-east-2.aws.neon.tech/neondb?sslmode=require`

---

## Step 2: Deploy the Backend API to Render

We will deploy the FastAPI backend using Render's free tier. Render compiles and runs the application using the [`backend/Dockerfile`](file:///c:/Users/KIIT/Desktop/AutoML/backend/Dockerfile) we configured.

### Instructions:
1. Initialize a new git repository in the `backend/` folder (or push your main repo to GitHub containing the backend directory).
2. Go to [render.com](https://render.com/) and log in (sign up for free if you don't have an account).
3. Click **New +** and select **Web Service**.
4. Connect your GitHub repository.
5. Configure the web service:
   - **Name:** `automl-backend`
   - **Root Directory:** `backend` (This is critical: it tells Render to run the build inside the backend subdirectory)
   - **Language:** `Docker` (Render will automatically detect the Dockerfile)
   - **Instance Type:** `Free` (0.5 CPU, 512 MB RAM)
6. Add the following **Environment Variables** under the "Environment" tab:

   | Key | Value | Description |
   | :--- | :--- | :--- |
   | `DATABASE_URL` | `postgresql://...` (Your Neon connection string) | Directs database operations to the cloud Postgres |
   | `HF_SANDBOX_URL` | `LegitScarf/automl-sandbox` | Integrates with your Hugging Face Space |

7. Click **Create Web Service**. Wait 3–4 minutes for the Docker image to build and deploy. Once booted, copy the backend URL (e.g. `https://automl-backend.onrender.com`).

---

## Step 3: Deploy the Frontend to Vercel

We will deploy the React/Next.js UI to Vercel's free hobby tier.

### Instructions:
1. Go to [vercel.com](https://vercel.com/) and sign up / log in.
2. Click **Add New** -> **Project**.
3. Import your GitHub repository.
4. Configure the project:
   - **Framework Preset:** `Next.js`
   - **Root Directory:** `frontend` (Ensure this is set so Vercel compiles the UI inside the frontend folder)
5. Under **Environment Variables**, add the API endpoint pointing to your deployed Render URL:
   
   | Key | Value | Description |
   | :--- | :--- | :--- |
   | `NEXT_PUBLIC_API_URL` | `https://automl-backend.onrender.com` (Your Render URL) | Tells the UI where to send API requests |

6. Click **Deploy**. Vercel will compile the Next.js bundle and host it at a custom `.vercel.app` domain within 2 minutes.

---

## Step 4: Verification & Keep-Alive Strategy

1. Open your Vercel deployment URL, upload a CSV dataset, specify a target variable, and trigger the run.
2. Confirm the telemetry console maps live profiling outputs and Remote GPU sandbox execution logs in real-time.
3. **Uptime Monitoring:** Render free tier sleep-disables after 15 minutes of inactivity. To prevent cold start latency when demoing to recruiters:
   - Go to [cron-job.org](https://cron-job.org/) (free service).
   - Set up a cron job to ping your Render health-check route (`https://automl-backend.onrender.com/docs`) every 14 minutes.
   - This keeps your portfolio application warm and responsive.
