# Goal Description

Enhance the Agentic AutoML platform to support user-selected task types (Regression vs. Classification), specific model selections, dynamic target variable selection, and a programmatic accuracy/performance threshold evaluation (default 90%). If the model's accuracy/metric falls below 90%, the workflow will enter a self-correcting loop to automatically tune the hyperparameters.

All changes will be developed and tested in a new git branch named `models`.

## Architectural Study & Key Decisions

1. **User Interface (`app3.py`):**
   * **CSV File Upload:** Integrate `st.file_uploader` to accept raw CSV files. Save the uploaded file locally so both the streamlit process and the backend docker sandbox can access it.
   * **Dynamic Schema Parsing:** Once the CSV is uploaded, parse it using `pandas` to extract column headers.
   * **Task Type & Model Selection:** 
     * Implement a dropdown or radio button for **Task Type** (`Classification` or `Regression`).
     * Implement a dropdown for **Model Selection** listing the provided models. Automatically filter models based on the selected task type (e.g., `Linear Regression` for regression only, `Logistic Regression` and `Naive Bayes` for classification only, and others for both).
     * Provide a dropdown for **Target Variable** using the parsed CSV columns.
   * **Webhook Integration:** Extend the POST request payload to include:
     * `task_type` (e.g. `"classification"` or `"regression"`)
     * `selected_model` (e.g. `"XGBoost"`, `"Random Forest"`, etc.)
     * `min_threshold` (default `0.90`)

2. **Self-Correction & Hyperparameter Tuning Loop:**
   * **In-Script Tuning:** We will instruct the CodeGen Agent to generate Python code that performs train/test splits, fits the selected model class, and calculates the validation metric (Accuracy for classification, $R^2$ score for regression).
   * **Programmatic Metric Validation:**
     * The generated script must write the final validation metric to `stdout` in a structured format: `METRIC_SCORE: <value>`.
     * The n8n orchestrator workflow will be updated with an `Evaluation Gate` conditional node.
     * If `exit_code == 0` but `METRIC_SCORE < min_threshold`, the workflow loops back to the LLM agent, prompting it with: "The model achieved score X which is below the threshold of Y. Please update the hyperparameter grid search, feature scaling/engineering, or model parameters to optimize performance."
     * Up to 3 optimization loops will be allowed before failing or returning the best model.

3. **Sandbox Environment Enhancement:**
   * Update [Dockerfile](file:///c:/Users/KIIT/Desktop/AutoML/sandbox/Dockerfile) to support new ML models by adding packages: `lightgbm`, `catboost`.

---

## Proposed Changes

### [Component 1] Branch Creation & Testing Setup

#### [NEW] Git Branch Configuration
* Create and switch to the `models` branch:
  ```bash
  git checkout -b models
  ```

---

### [Component 2] Streamlit Frontend Layout

#### [MODIFY] [app3.py](file:///c:/Users/KIIT/Desktop/AutoML/app3.py)
* Add `st.file_uploader` for CSV upload.
* Add dropdowns for `task_type`, `selected_model` (filtered), and `target_variable` (loaded dynamically).
* Pass `task_type`, `selected_model`, and `min_threshold` (set to `0.90` by default) in the webhook JSON payload.

---

### [Component 3] n8n Orchestrator Workflow

#### [MODIFY] [automl_workflow.json](file:///c:/Users/KIIT/Desktop/AutoML/n8n/automl_workflow.json)
* Update the Webhook Trigger node definition to receive the new parameters.
* Update the CodeGen prompt to instruct the agent to generate scripts using the selected model, compute the correct metric, handle hyperparameter tuning (GridSearchCV/RandomizedSearchCV), and output the structured score string.
* Add a conditional decision node checking if the metric score is less than `min_threshold`. If yes, route back to the Optimization/Debug Agent.

---

### [Component 4] Execution Sandbox

#### [MODIFY] [Dockerfile](file:///c:/Users/KIIT/Desktop/AutoML/sandbox/Dockerfile)
* Install `lightgbm` and `catboost` to support the full range of user-selectable models.

---

## Verification Plan

### Automated Tests
* Create/update integration tests in `tests/test_core_pipeline.py` to:
  * Validate that the workspace can run classification and regression tasks.
  * Verify that a training run with low accuracy properly loops back for hyperparameter tuning.

### Manual Verification
* Run the Streamlit dashboard on the `models` branch.
* Upload a sample CSV, select a task type, model class, and verify the model tuning loop kicks in if threshold is set high.
