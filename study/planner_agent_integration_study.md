# Architectural Study: Multi-Agent Planner Integration in Omega

This study analyzes the introduction of a **Planner Agent** into the Omega AutoML pipeline. The planner sits between the dataset profiling and code generation stages, creating a statistical checklist tailored to the target model's assumptions and the dataset's characteristics.

---

## 1. Architectural Changes

We propose migrating from a single-stage CodeGen pipeline to a **Two-Agent Orchestration Flow**:

```
[ Dataset Uploaded ]
        │
        ▼
[ Profiler Agent ] ──► Extracts column types, missing values, dimensions
        │
        ▼
[ Planner Agent ]  ──► Analyzes model type & profile metadata.
        │              Generates a step-by-step statistical plan (e.g. VIF checks, residual plots).
        ▼
[ Coder Agent ]    ──► Receives the Plan + Profile.
        │              Translates the steps into a real, syntax-valid Python script.
        ▼
[ HF Sandbox ]     ──► Executes script, trains model, exports metrics + diagnostic plots.
```

---

## 2. Pros & Cons Analysis

### Pros
1. **Statistical Rigor:** Standard AutoML tools typically skip assumptions validation. For linear models, verifying multicollinearity (VIF) and residual behavior prevents users from deploying statistically invalid models.
2. **Dynamic Explainability:** The plan can be logged in the database and rendered on the frontend telemetry stream, giving users full visibility into the agent's reasoning.
3. **Fewer Code Hallucinations:** Breaking the process into "what to do" (Planner) and "how to write it in Python" (Coder) drastically increases code generation accuracy.
4. **Rich Artifact Packages:** By planning visualization steps (e.g., residual plots, coefficient weight bar charts), the final output ZIP bundle will now contain graphic assets (`residuals.png`, `coefficients.png`) along with raw model weights.

### Cons
1. **Added Latency:** Running an extra agent planning cycle adds 2–4 seconds of orchestration overhead.
2. **State Tracking Complexity:** The database schema must be updated to store and track the plan.

---

## 3. Core Database & State Changes

### A. Run Status States
We will insert a new state `planning` between `profiling` and `generating`:
* `pending` ➔ `profiling` ➔ **`planning`** ➔ `generating` ➔ `training` ➔ `verifying` ➔ `complete`/`failed`.

### B. SQLAlchemy Model Updates ([`backend/models.py`](file:///c:/Users/KIIT/Desktop/AutoML/backend/models.py)):
We will add a new column to store the generated plan string:
```python
class AutoMLRun(Base):
    # ... existing columns ...
    plan = Column(Text, nullable=True) # Detailed step-by-step text plan
```

---

## 4. Modeling the Planner Steps (Example: Linear Regression)

If the user selects **Linear Regression**, the Planner will generate a 10-step plan based on classical statistical assumptions (matching your notebook notes):

1. **Import Libraries & Data:** Load pandas, numpy, sklearn linear model, and decode the embedded dataset.
2. **Multicollinearity Checks (VIF):** Calculate Variance Inflation Factors. Drop any features exceeding a VIF threshold of 5.0 to handle collinearity.
3. **Feature Scaling:** Scale remaining numeric features using Scikit-Learn's `StandardScaler`.
4. **Data Partitioning:** Split data into an 80/20 train/test split.
5. **Model Fitting:** Instantiate and fit `LinearRegression`.
6. **Inference:** Make predictions on the validation test set.
7. **Evaluation:** Calculate R2 score, Mean Absolute Error (MAE), and Mean Squared Error (MSE).
8. **Residual Diagnostics:** Calculate prediction residuals ($y_{test} - y_{pred}$) and save a residual distribution histogram as `residuals.png`.
9. **Assumption Verifications:** Check homoscedasticity and residual normality.
10. **Coefficient Interpretation:** Plot feature coefficients in a bar chart and save it as `coefficients.png` to interpret feature weights.
