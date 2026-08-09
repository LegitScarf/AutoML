# Implementation Plan: Foolproof Generation of Model Bundle Artifacts

This plan details how we will modify the sandbox environment, agent prompts, and backend packaging logic to guarantee that every run outputs the full 5-file bundle:
1. `model.pkl` (Trained classifier/regressor)
2. `preprocessor.pkl` (Fitted preprocessing pipeline)
3. `requirements.txt` (Environment specification)
4. `inference.py` (Plug-and-play prediction script)
5. `training_report.pdf` (Visual quality report)

---

## Proposed Changes

### [Component 1] Sandbox Environment
We need to add reporting and plotting libraries to the Sandbox execution image so scripts can render PDF reports and evaluation charts.

#### [MODIFY] [Dockerfile](file:///c:/Users/KIIT/Desktop/AutoML/sandbox/Dockerfile)
* Install `reportlab` (for PDF generation), `matplotlib` and `seaborn` (for evaluation plotting).

---

### [Component 2] CodeGen Prompt (n8n Workflow)
We must instruct the CodeGen agent explicitly on the exact structure, file names, and contents of the 5 required files.

#### [MODIFY] [automl_workflow.json](file:///c:/Users/KIIT/Desktop/AutoML/n8n/automl_workflow.json)
* Update the prompt of the **CodeGen Agent** to command the generation of:
  * `model.pkl` & `preprocessor.pkl` (separating feature scaling/imputation from model fitting).
  * `inference.py` containing a load function and a prediction function.
  * `requirements.txt` with package versions.
  * `training_report.pdf` using `reportlab` to render text, stats, and saved `matplotlib` score plots.

---

### [Component 3] Backend Zipping Service
Update the zipping routine to ensure all 5 files are verified, collected, and added to the download package.

#### [MODIFY] [automl_service.py](file:///c:/Users/KIIT/Desktop/AutoML/mcp_servers/automl_service.py)
* Update the list of files packaged in the zip archive to include all 5 filenames.
* Ensure robust path resolution for all output files.

---

## Verification Plan

### Automated Tests
* Run the test suite to verify the mock generator outputs all files successfully:
  ```bash
  $env:PYTHONPATH="."; .venv\Scripts\pytest tests/test_core_pipeline.py
  ```

### Manual Verification
* Run a training run through Streamlit and extract the downloaded `automl_bundle.zip` to confirm it contains all 5 files.
