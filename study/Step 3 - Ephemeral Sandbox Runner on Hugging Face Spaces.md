# Implementation Plan: Step 3 - Ephemeral Sandbox Runner on Hugging Face Spaces

This plan outlines the design of the heavy-compute sandbox environment. Since Render’s free tier lacks the memory to train ML models (512MB RAM limit), we delegate training, profiling, and artifact packaging to a free Hugging Face Docker Space (16GB RAM limit).

---

## Technical Flow Diagram

```
[Render Backend API] ---> Triggers ---> [Hugging Face Space API (FastAPI)]
                                           |
                                           +---> Runs Python Subprocess (16GB RAM)
                                           |
[Supabase Storage]   <--- Uploads Artifacts <----+
                                           |
[Render Backend API] <--- Returns Status --+
```

---

## Proposed Changes

We will create a `sandbox` directory in the root containing files for our Hugging Face Space.

### [Component 1] Sandbox FastAPI Server

#### [NEW] [sandbox/app.py](file:///c:/Users/KIIT/Desktop/AutoML/sandbox/app.py)
* A FastAPI server running inside the Hugging Face Space:
  * `POST /profile`: Receives a dataset URI, downloads it, parses shape, data types, and null configurations, returning a JSON report.
  * `POST /execute`: Receives python training code, writes it to an ephemeral file, executes it in a monitored python subprocess, and captures `stdout`/`stderr` logs.
  * `POST /package`: Gathers `model.pkl`, `preprocessor.pkl`, `requirements.txt`, `inference.py`, and the training PDF, bundles them into a zip, uploads it to Supabase Storage, and returns the download link.

---

### [Component 2] Containerization & Dependencies

#### [NEW] [sandbox/Dockerfile](file:///c:/Users/KIIT/Desktop/AutoML/sandbox/Dockerfile)
* Docker image customized for Hugging Face Spaces:
  * Exposes port `7860` (default port for Hugging Face Spaces).
  * Pre-installs key ML libraries: `scikit-learn`, `pandas`, `numpy`, `xgboost`, `lightgbm`, `catboost`, `matplotlib`, `seaborn`, `reportlab` (for PDF reports).

#### [NEW] [sandbox/requirements.txt](file:///c:/Users/KIIT/Desktop/AutoML/sandbox/requirements.txt)
* Server dependencies: `fastapi`, `uvicorn`, `requests`, `supabase`, `pandas`, `numpy`, `scikit-learn`, `xgboost`, `reportlab`, `joblib`.

---

## Verification Plan

### Local Mock Execution
* Run the FastAPI sandbox locally:
  ```bash
  cd sandbox
  pip install -r requirements.txt
  uvicorn app:app --port 7860
  ```
* Test `/execute` endpoint using curl/Postman to run a dummy training script, validating that execution results and exit codes are returned correctly.

### Hugging Face Deployment Verification
* Create a free Hugging Face Docker Space.
* Push `sandbox/` contents to Hugging Face Git remote.
* Trigger a test AutoML pipeline run from the local backend to verify communication with the HF space.
