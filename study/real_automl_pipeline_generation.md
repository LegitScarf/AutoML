# Technical Study: Real AutoML Pipeline Generation & Artifact ZIP Completeness

This study investigates the current hardcoded mock code generation in Omega and outlines the transition to a dynamic, real machine learning pipeline generator.

---

## 1. Current System Limitations

### A. Dummy Training Data and Models
In the initial orchestrator design, `backend/orchestrator.py` generated a static Python string that created random data arrays (`np.random.rand`) instead of consuming the user's uploaded dataset:
```python
X = np.random.rand(100, 5)
y = np.random.randint(0, 2, 100) if "{task}" == "classification" else np.random.rand(100)
```
Consequently:
* The model trained was a dummy model fitting random noise.
* It only learned on 5 features, regardless of the dimensions of your uploaded CSV.

### B. Ephemeral Sandbox File Restrictions
The sandbox runs in a separate, isolated Hugging Face container space. The container has no network access to your local files or Postgres database. Therefore, the training script could not read the uploaded CSV from disk or a database URL.

### C. Missing ZIP Artifacts
Because the training script only fit a dummy model on random variables, it saved only `model.pkl`. It did not produce:
1. `preprocessor.pkl`: Essential for scaling numeric fields and one-hot encoding categories.
2. `requirements.txt`: The version map of the runtime libraries.
3. `README.md`: Step-by-step instructions on loading the model and making predictions.

---

## 2. Proposed Architecture for Real AutoML

To bridge the actual uploaded dataset into the sandbox and build a production-grade bundle, we will implement the following:

```
[ FastAPI Backend ]
  1. Reads uploaded dataset columns, types, and labels.
  2. Encodes actual CSV content to base64.
  3. Formulates a dynamic, model-specific training script embedding the CSV base64 string.
       │
       ▼ (Submits Script Code)
[ HF Sandbox Container ]
  1. Decodes base64 string back into CSV memory.
  2. Builds Scikit-Learn `ColumnTransformer` (scaling, imputing, categorical encoding).
  3. Splits data, trains model (RandomForest, XGBoost, LightGBM, etc.).
  4. Saves `model.pkl` and `preprocessor.pkl` to directory.
  5. Generates `requirements.txt` and a usage guide `README.md`.
  6. Compresses all 4 files into `{run_id}.zip`.
```

---

## 3. Dynamic Pipeline Template Design

The generated python script will dynamically import and instantiate models:
* **Preprocessing:** Handles missing values and categories.
  ```python
  from sklearn.compose import ColumnTransformer
  from sklearn.preprocessing import StandardScaler, OneHotEncoder
  from sklearn.impute import SimpleImputer
  # Numeric & Categorical Pipelines are fit on actual column types
  ```
* **Base64 CSV Loader:**
  ```python
  import base64
  import io
  CSV_BASE64 = "<base64_encoded_data>"
  df = pd.read_csv(io.StringIO(base64.b64decode(CSV_BASE64).decode('utf-8')))
  ```
* **Dynamic Model Imports:**
  Loads the user's selected algorithm (e.g. `xgboost`, `lightgbm`, or `scikit-learn` linear/ensemble models).
