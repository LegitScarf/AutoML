# Implementation Plan: Custom Model Artifact ZIP Downloads

This plan addresses the bottleneck where trained model artifacts (like `model.pkl`) generated in the Hugging Face Space sandbox are not packaged or sent back to the API gateway, preventing users from downloading their custom trained models.

---

## 1. Root Cause Analysis
* **Local Isolation:** The python training script executes in the Hugging Face container space and saves files locally (e.g. `model.pkl`).
* **Missing Bridge:** The Render backend queries the `/execute` API endpoint, receiving only `stdout`, `stderr`, and `exit_code`. It does not retrieve the binary model files.
* **Hardcoded Link:** The `bundle_url` is currently hardcoded to a static URL `https://huggingface.co/spaces/.../model.pkl` which does not contain the custom trained model and requires user authentication.

---

## 2. Proposed Architecture

```
[ HF Space Sandbox ] 
  1. Runs training script in isolated Temp Directory.
  2. Zips all output files (*.pkl, *.py, *.pdf) in-memory.
  3. Returns ZIP archive as base64 string in API response.
       │
       ▼ (Base64 String)
[ Render FastAPI Backend ]
  1. Decodes base64 string.
  2. Saves binary ZIP file to `static/bundles/{run_id}.zip`.
  3. Returns relative download path `/static/bundles/{run_id}.zip`.
       │
       ▼ (Relative URL)
[ Vercel Next.js UI ]
  1. Detects relative path and prepends the backend host URL.
  2. Exposes a working, direct download link for the custom ZIP file.
```

---

## 3. Proposed Changes

### [Component 1] Sandbox Zipping Logic
#### [MODIFY] [sandbox/app.py](file:///c:/Users/KIIT/Desktop/AutoML/sandbox/app.py)
* Update `run_script_in_sandbox` to execute the code inside a temporary directory (`tempfile.TemporaryDirectory`).
* Gather all files generated in that directory (such as `.pkl`, `.py`, `.pdf`, `.png` files).
* Zip them in-memory using `zipfile.ZipFile` and `io.BytesIO`.
* Encode the zip bytes to a base64 string and return it in the JSON response under the key `zip_base64`.

### [Component 2] FastAPI Static File Hosting
#### [MODIFY] [backend/main.py](file:///c:/Users/KIIT/Desktop/AutoML/backend/main.py)
* Import `StaticFiles` from `fastapi.staticfiles`.
* Ensure the directory `backend/static/bundles` is created on startup.
* Mount `/static` route using `app.mount("/static", StaticFiles(directory="static"), name="static")`.

### [Component 3] Orchestrator Decoding & Stash
#### [MODIFY] [backend/orchestrator.py](file:///c:/Users/KIIT/Desktop/AutoML/backend/orchestrator.py)
* In `run_automl_pipeline`, after receiving `exec_res`, check for the presence of the `zip_base64` string.
* Decode the base64 string and write the raw binary bytes to `static/bundles/{run_id}.zip`.
* Update `run.bundle_url` to reference `/static/bundles/{run_id}.zip` instead of the hardcoded Hugging Face URL.

### [Component 4] Frontend Download Mapping
#### [MODIFY] [frontend/app/page.js](file:///c:/Users/KIIT/Desktop/AutoML/frontend/app/page.js)
* Update the `pollInterval` logic. If `data.bundle_url` starts with `/`, prepend the configured `backendUrl` before setting the `downloadUrl` state.

---

## 4. Verification Plan

### Automated Tests
* Test that the sandbox zipping logic executes correctly by running a dummy python script.
* Test that FastAPI mounts static folders.

### Manual Verification
* Run a pipeline training loop locally, verify the generated ZIP file is created under `backend/static/bundles/`, and check that the download button downloads a valid ZIP file containing `model.pkl` and `model_training.py`.
