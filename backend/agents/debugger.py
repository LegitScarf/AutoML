import re
from .config import get_openai_client, OPENAI_MODEL

def ask_debugger_agent(original_code: str, error_context: str, plan: str) -> str:
    """
    Queries OpenAI gpt-5.6-luna with the failed code and error context to
    debug or optimize the script. Returns pure repaired Python code.
    """
    client = get_openai_client()
    
    prompt = f"""You are a senior Machine Learning Debugger & Optimization Agent. An execution attempt of the model training script failed or did not meet performance metrics.
Your job is to rewrite the Python script to resolve this issue.

---
## Error / Performance Context:
{error_context}

---
## Original Code to Debug/Optimize:
```python
{original_code}
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
    
    return code.strip()
