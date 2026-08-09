# Implementation Plan: Step 2 - Database Schema & Backend API on Render

This plan outlines the architecture and deployment structure for the **AutoML Backend** on Render's Free Tier, integrated with a serverless Postgres database (Neon/Supabase) and a remote 16GB RAM training sandbox (Hugging Face Spaces) to work around Render's 512MB memory limitation.

---

## Technical Architecture Overview

To run 100% free of charge without crashing, we decouple the control plane (API and state) from the data plane (ML training):

1. **FastAPI Backend (Render):** Lightweight API that handles file uploading, manages run history, and orchestrates the pipeline workflow. It consumes <100MB of RAM.
2. **Postgres Database (Neon/Supabase):** Keeps a permanent record of all training runs, telemetry logs, and metrics.
3. **Execution Sandbox (Hugging Face Spaces):** Ephemeral compute instance with 16GB RAM that receives the training script, runs the execution loop, and uploads output files to cloud storage.

---

## Proposed Changes

We will create a `backend` directory in the root folder containing the FastAPI application.

### [Component 1] Database Integration & Schema

#### [NEW] [backend/db/schema.sql](file:///c:/Users/KIIT/Desktop/AutoML/backend/db/schema.sql)
* SQL script to initialize the database tables:
  ```sql
  CREATE TABLE IF NOT EXISTS runs (
      id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
      created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
      dataset_name VARCHAR(255) NOT NULL,
      target_variable VARCHAR(255) NOT NULL,
      task_type VARCHAR(50) NOT NULL,
      selected_model VARCHAR(100),
      min_threshold FLOAT,
      status VARCHAR(50) DEFAULT 'pending', -- pending, running, success, failed
      metrics JSONB DEFAULT '{}'::jsonb,
      logs TEXT[] DEFAULT ARRAY[]::text[],
      bundle_url VARCHAR(512)
  );
  ```

#### [NEW] [backend/db/database.py](file:///c:/Users/KIIT/Desktop/AutoML/backend/db/database.py)
* Database connection manager using `SQLAlchemy` or `asyncpg` to interface with the serverless Postgres connection string.

---

### [Component 2] FastAPI Server Core

#### [NEW] [backend/main.py](file:///c:/Users/KIIT/Desktop/AutoML/backend/main.py)
* Exposed REST endpoints for the frontend UI:
  * `POST /api/upload`: Accepts a CSV file, uploads it to Supabase Storage, and registers a `pending` run ID.
  * `POST /api/runs/{run_id}/trigger`: Starts an asynchronous training task.
  * `GET /api/runs`: Lists history of all AutoML runs (for portfolio demonstration).
  * `GET /api/runs/{run_id}/status`: Returns the current active step, logs list, and output metrics for polling.

#### [NEW] [backend/orchestrator.py](file:///c:/Users/KIIT/Desktop/AutoML/backend/orchestrator.py)
* Contains the async workflow runner:
  1. Requests profiling data from the profiling service.
  2. Submits details to the LLM agent to generate code.
  3. POSTs the code execution request to the Hugging Face Docker Sandbox.
  4. Updates the database states dynamically at each step.

---

### [Component 3] Docker Packaging for Render

#### [NEW] [backend/Dockerfile](file:///c:/Users/KIIT/Desktop/AutoML/backend/Dockerfile)
* Standard Dockerfile targeting Python 3.11-slim.
* Optimizes startup layers to keep build times on Render under 3 minutes.

#### [NEW] [backend/requirements.txt](file:///c:/Users/KIIT/Desktop/AutoML/backend/requirements.txt)
* FastAPI dependencies: `fastapi`, `uvicorn`, `sqlalchemy`, `psycopg2-binary`, `requests`, `supabase-py`.

---

## Verification Plan

### Automated/Local Tests
* Spin up a local Postgres instance (or use a test Neon URL).
* Execute local server runs:
  ```bash
  cd backend
  pip install -r requirements.txt
  uvicorn main:app --reload
  ```
* Verify api endpoints using Swagger docs (`http://localhost:8000/docs`).

### Manual Verification
* Upload a sample CSV to the `/api/upload` endpoint and verify the entry appears in the database.
* Mock the Hugging Face Space endpoint and verify that the async orchestrator updates status fields from `profiling` to `generating` to `complete`.
