import re
from .config import get_openai_client, OPENAI_MODEL

def ask_debugger_agent(original_code: str, error_context: str, plan: str, csv_base64: str = "") -> str:
    """
    Queries OpenAI gpt-5.6-luna with the failed code and error context to
    debug or optimize the script. Strips raw dataset base64 from prompt to prevent
    exceeding token limits, then re-injects the dataset string into the repaired code.
    """
    client = get_openai_client()

    # Extract base64 dataset if present in original code
    if not csv_base64:
        match = re.search(r'CSV_BASE64\s*=\s*["\']([^"\']+)["\']', original_code)
        if match and match.group(1) != "__CSV_BASE64_DATA__":
            csv_base64 = match.group(1)

    # Sanitize out the massive base64 payload to keep prompt small
    sanitized_code = re.sub(r'CSV_BASE64\s*=\s*["\'][^"\']*["\']', 'CSV_BASE64 = "__CSV_BASE64_DATA__"', original_code)
    
    prompt = f"""You are a senior Machine Learning Debugger & Optimization Agent. An execution attempt of the model training script failed or did not meet performance metrics.
Your job is to rewrite the Python script to resolve this issue.
The dataset is loaded from memory via `CSV_BASE64 = "__CSV_BASE64_DATA__"`. Keep that exact placeholder in the code.

---
## Error / Performance Context:
{error_context}

---
## Original Code to Debug/Optimize:
```python
{sanitized_code}
```

---
## Original Training Plan:
{plan}

---
## Instructions:
1. **Analyze Failure:** 
   - If it was a runtime crash (SyntaxError, ValueError, KeyError, etc.), fix the logic bug, handles missing values, or ensure shapes align correctly.
   - If the score fell below the target threshold, increase the search space, add hyperparameter search parameters (e.g. RandomizedSearchCV or a grid search with wider settings), implement robust scaling, or perform feature engineering.
2. **Output Formatting:** Return ONLY the complete, corrected Python script. Do NOT include markdown blocks, explanation text, or code block fences (```python). The output must be immediately executable.
"""

    response = client.chat.completions.create(
        model=OPENAI_MODEL,
        messages=[
            {"role": "system", "content": "You are a senior debugging assistant that writes repaired, error-free machine learning code."},
            {"role": "user", "content": prompt}
        ]
    )
    
    code = response.choices[0].message.content.strip()
    
    # Strip markdown fences if present
    code = re.sub(r"^```python\s*", "", code, flags=re.IGNORECASE)
    code = re.sub(r"^```\s*", "", code)
    code = re.sub(r"\s*```$", "", code)
    
    # Re-inject the base64 string
    if csv_base64:
        if "__CSV_BASE64_DATA__" in code:
            code = code.replace("__CSV_BASE64_DATA__", csv_base64)
        elif "CSV_BASE64" in code:
            code = re.sub(r'CSV_BASE64\s*=\s*["\'][^"\']*["\']', f'CSV_BASE64 = "{csv_base64}"', code)
        else:
            dataset_preamble = (
                f'import base64\nimport io\nimport pandas as pd\n'
                f'CSV_BASE64 = "{csv_base64}"\n'
                f'df = pd.read_csv(io.StringIO(base64.b64decode(CSV_BASE64).decode("utf-8")))\n'
            )
            code = dataset_preamble + code

    return code.strip()
