# Architectural Study & Fix Plan: Native Gradio API on ZeroGPU

This document outlines the architectural study of Hugging Face's ZeroGPU Gradio integration limits, and presents the plan to implement a native Gradio API to solve the "No @spaces.GPU function detected" error permanently on the free tier.

---

## 1. Architectural Study of the Root Cause

### Why the ZeroGPU Error Persisted
Hugging Face ZeroGPU requires any Space running on the free tier to be a **Gradio SDK-first** application.
* **Gradio's Startup Pipeline:** When Hugging Face launches a Gradio SDK Space, it imports `app.py`, wraps the `Blocks` event triggers with ZeroGPU allocation hooks, and calls `demo.launch()`.
* **Our Conflict:** To support our backend REST endpoints (`/profile`, `/execute`), we used `gr.mount_gradio_app(api, demo)` and launched a manual FastAPI server using `uvicorn.run()`.
* **The Crash:** Because we ran Uvicorn directly, Gradio's native startup hooks were bypassed. ZeroGPU failed to initialize, resulting in the `No @spaces.GPU function detected during startup` crash.

---

## 2. The Solution: Gradio's Native API Engine

Every Gradio interface automatically exposes its click-events as **programmatic REST API endpoints** when the `api_name` parameter is specified in the event binder.

By leveraging this built-in capability:
1. We let Hugging Face launch the Gradio `demo` Blocks naturally (no custom Uvicorn process or custom FastAPI app needed).
2. The ZeroGPU manager detects the `@spaces.GPU` decorator on the click-event and initializes successfully.
3. Gradio automatically registers public REST endpoints (`/api/profile` and `/api/execute`).
4. Our FastAPI backend can call these sandbox endpoints using the official, lightweight `gradio_client` library.

---

## 3. Implementation Steps

### Step 1: Update [`sandbox/app.py`](file:///c:/Users/KIIT/Desktop/AutoML/sandbox/app.py)
We will rewrite [`sandbox/app.py`](file:///c:/Users/KIIT/Desktop/AutoML/sandbox/app.py) to declare a clean, standard Gradio application without FastAPI mounting or Uvicorn launching:

```python
import sys
import types
import os

# 1. Pre-register mock 'spaces' module if not installed (for local environments)
try:
    import spaces
except ImportError:
    mock_spaces = types.ModuleType("spaces")
    mock_spaces.GPU = lambda func: func
    sys.modules["spaces"] = mock_spaces

# 2. Top-level unconditional import for HF ZeroGPU static AST analyzer
import spaces

import tempfile
import subprocess
import pandas as pd
import gradio as gr

def profile_dataset(file_path):
    """Pandas profiling helper"""
    if not file_path or not file_path.endswith(('.csv', '.xlsx')):
        return {"error": "Invalid file format. Upload CSV or Excel."}
    try:
        df = pd.read_csv(file_path) if file_path.endswith('.csv') else pd.read_excel(file_path)
        return {
            "num_rows": df.shape[0],
            "num_cols": df.shape[1],
            "dtypes": {col: str(dtype) for col, dtype in df.dtypes.items()},
            "missing_counts": df.isnull().sum().to_dict(),
            "numeric_columns": list(df.select_dtypes(include='number').columns),
            "categorical_columns": list(df.select_dtypes(exclude='number').columns),
        }
    except Exception as e:
        return {"error": str(e)}

@spaces.GPU
def run_script_in_sandbox(script_content: str, timeout: int = 60):
    """GPU-enabled training runner"""
    with tempfile.NamedTemporaryFile(suffix=".py", delete=False, mode="w", encoding="utf-8") as tmp:
        tmp.write(script_content)
        temp_path = tmp.name
    try:
        res = subprocess.run([sys.executable, temp_path], capture_output=True, text=True, timeout=timeout)
        return {"exit_code": res.returncode, "stdout": res.stdout, "stderr": res.stderr}
    except subprocess.TimeoutExpired:
        return {"exit_code": -1, "stdout": "", "stderr": f"Timed out after {timeout}s."}
    except Exception as e:
        return {"exit_code": -2, "stdout": "", "stderr": str(e)}
    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)

# UI layout containing the endpoints
with gr.Blocks(title="AutoML Sandbox", theme=gr.themes.Soft()) as demo:
    gr.Markdown("# 🤖 AutoML Sandbox Runner")
    gr.Markdown("✅ **Sandbox is online.**")
    
    # 1. Profile Endpoint
    file_input = gr.File(label="Upload Dataset", file_types=[".csv", ".xlsx"], visible=False)
    profile_output = gr.JSON(label="Profile JSON", visible=False)
    profile_btn = gr.Button("Profile", visible=False)
    profile_btn.click(fn=profile_dataset, inputs=file_input, outputs=profile_output, api_name="profile")
    
    # 2. Execute Endpoint
    script_input = gr.Textbox(label="Python Script", visible=False)
    timeout_input = gr.Number(value=60, label="Timeout", visible=False)
    execute_output = gr.JSON(label="Execution Output", visible=False)
    execute_btn = gr.Button("Execute", visible=False)
    execute_btn.click(fn=run_script_in_sandbox, inputs=[script_input, timeout_input], outputs=execute_output, api_name="execute")

if __name__ == "__main__":
    demo.launch(server_name="0.0.0.0", server_port=7860)
```

---

### Step 2: Add `gradio_client` to Backend Dependencies

We will append the official `gradio-client` package to [`backend/requirements.txt`](file:///c:/Users/KIIT/Desktop/AutoML/backend/requirements.txt):

```diff
  httpx==0.27.0
+ gradio-client==1.5.2
```

---

### Step 3: Update Orchestrator to use Gradio Client

We will update [`backend/orchestrator.py`](file:///c:/Users/KIIT/Desktop/AutoML/backend/orchestrator.py) to trigger sandbox calls via the Gradio Client API:

```python
from gradio_client import Client

def run_script_remotely(script_content: str, timeout: int):
    client = Client("LegitScarf/automl-sandbox")
    result = client.predict(
        script_content=script_content,
        timeout=timeout,
        api_name="/execute"
    )
    return result # Returns {"exit_code": int, "stdout": str, "stderr": str}
```

---

## 4. Verification Plan

1. Push the updated `app.py` to the existing Space.
2. Verify it builds and changes to **Running** status (since it runs native Gradio).
3. Test locally in our backend environment that the client triggers predictions successfully on the ZeroGPU node.
