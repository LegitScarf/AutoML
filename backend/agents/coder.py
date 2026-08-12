import re
from .config import get_openai_client, OPENAI_MODEL

def ask_coder_agent(model_name: str, task: str, target: str, plan: str, csv_base64: str, numeric_cols: list, categorical_cols: list) -> str:
    """
    Queries OpenAI gpt-5.6-luna to translate the statistical plan checklist and
    raw base64 dataset into a single, fully functional python training script.
    """
    client = get_openai_client()
    
    # We pass the full base64 dataset but show the code snippet structure in instructions
    prompt = f"""You are a senior Machine Learning Code Generation Agent. Your job is to translate a structured data science plan into a single, clean, highly robust Python script.

## Core Rules:
1. **Load Dataset from Memory:** You must decode the embedded base64 CSV string inside the script using Python's `base64` and `io.StringIO` packages.
   ```python
   import base64
   import io
   CSV_BASE64 = "{csv_base64[:40]}... (truncated)"
   csv_data = base64.b64decode(CSV_BASE64).decode('utf-8')
   df = pd.read_csv(io.StringIO(csv_data))
   ```
2. **Handle Preprocessing pipelines:** Create a Scikit-Learn `ColumnTransformer` with `Pipeline` to impute missing values (mean for numeric, most frequent for categorical) and transform features (StandardScaler for numeric, OneHotEncoder(handle_unknown='ignore') for categorical).
3. **Multicollinearity Checks (VIF):** If this is a linear model (Linear Regression, Logistic Regression), write a lightweight loop to calculate VIF dynamically using a linear regression model (to avoid external packages like statsmodels) and drop features where VIF > 5.0 before training.
4. **Data Partitioning:** Split data into an 80/20 train/test split. Fit the preprocessor on the train set and transform both train and test sets (prevent data leakage!).
5. **Dynamic Model Imports:** Import the model matching `{model_name}`. Instantiation must align with the `{task}` task type.
6. **Print Metrics to Stdout:** Calculate validation scores. You MUST print the metrics with a special `[METRIC]` prefix:
   - For classification: `print(f"[METRIC] Accuracy = {{acc:.4f}}")`
   - For regression: `print(f"[METRIC] R2 Score = {{r2:.4f}}")` (also print MAE and RMSE)
7. **Write Visualizations as PNG files:** 
   - For classification: Plot a Confusion Matrix heatmap and top Feature Importances bar chart. Save them as `confusion_matrix.png` and `feature_importances.png`.
   - For regression: Plot a residuals distribution histogram and top coefficients/importances. Save them as `residuals.png` and `coefficients.png`.
   - Always call `plt.tight_layout()`, save using `plt.savefig("filename.png")`, and call `plt.close()` to prevent memory leaks.
8. **Export Requirements & README:** The script must write a `requirements.txt` containing dependencies and a markdown `README.md` guide explaining how to load `model.pkl` and `preprocessor.pkl`.
9. **No Markdown Fences:** Do NOT wrap the script inside markdown block fences (such as ```python ... ```). Return ONLY raw executable Python code.

---
## Detailed Plan Checklist to Implement:
{plan}

---
## Dataset Details:
* **Target Variable:** {target}
* **Task Type:** {task}
* **Numeric Columns:** {repr(numeric_cols)}
* **Categorical Columns:** {repr(categorical_cols)}
* **Base64 Dataset Data:**
CSV_BASE64 = "{csv_base64}"
"""

    response = client.chat.completions.create(
        model=OPENAI_MODEL,
        messages=[
            {"role": "system", "content": "You are a master Python programmer that writes syntax-perfect, standalone machine learning scripts."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.0
    )
    
    code = response.choices[0].message.content.strip()
    
    # Post-process to remove markdown fences if the LLM outputted them despite instructions
    code = re.sub(r"^```python\s*", "", code, flags=re.IGNORECASE)
    code = re.sub(r"^```\s*", "", code)
    code = re.sub(r"\s*```$", "", code)
    
    return code.strip()
