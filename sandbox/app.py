import sys
import types
import os

# Monkey patch gradio_client schema parsing bug (TypeError: argument of type 'bool' is not iterable)
try:
    import gradio_client.utils
    orig_get_type = gradio_client.utils.get_type
    def patched_get_type(schema):
        if isinstance(schema, bool):
            return "boolean"
        return orig_get_type(schema)
    gradio_client.utils.get_type = patched_get_type
except Exception:
    pass


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

import json

def profile_dataset(file_path):
    """
    Ingests and profiles dataset using Pandas, returning schema and summary statistics.
    """
    if not file_path:
        return json.dumps({"error": "No file uploaded."})
    
    # Resolve actual file path if passed as Gradio FileData dict/object
    actual_path = None
    if isinstance(file_path, str):
        actual_path = file_path
    elif isinstance(file_path, dict):
        actual_path = file_path.get("path") or file_path.get("name")
    elif hasattr(file_path, "path"):
        actual_path = file_path.path
    elif hasattr(file_path, "name"):
        actual_path = file_path.name
        
    if not actual_path:
        return json.dumps({"error": "Failed to resolve uploaded file path."})
        
    if not actual_path.endswith(('.csv', '.xlsx')):
        return json.dumps({"error": f"Unsupported file format. Path: {actual_path}"})
        
    try:
        if actual_path.endswith('.csv'):
            df = pd.read_csv(actual_path)
        else:
            df = pd.read_excel(actual_path)
            
        res = {
            "num_rows": df.shape[0],
            "num_cols": df.shape[1],
            "dtypes": {col: str(dtype) for col, dtype in df.dtypes.items()},
            "missing_counts": df.isnull().sum().to_dict(),
            "numeric_columns": list(df.select_dtypes(include='number').columns),
            "categorical_columns": list(df.select_dtypes(exclude='number').columns),
        }
        return json.dumps(res)
    except Exception as e:
        return json.dumps({"error": f"Failed to profile dataset: {str(e)}"})

@spaces.GPU
def run_script_in_sandbox(script_content: str, timeout: int = 60):
    """
    Executes the training script inside an isolated python subprocess,
    returning stdout, stderr, and exit_code.
    """
    with tempfile.NamedTemporaryFile(suffix=".py", delete=False, mode="w", encoding="utf-8") as tmp:
        tmp.write(script_content)
        temp_path = tmp.name

    try:
        res = subprocess.run(
            [sys.executable, temp_path],
            capture_output=True,
            text=True,
            timeout=timeout,
        )
        out = {"exit_code": res.returncode, "stdout": res.stdout, "stderr": res.stderr}
        return json.dumps(out)
    except subprocess.TimeoutExpired:
        return json.dumps({"exit_code": -1, "stdout": "", "stderr": f"Timed out after {timeout}s."})
    except Exception as e:
        return json.dumps({"exit_code": -2, "stdout": "", "stderr": str(e)})
    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)

# UI layout containing the API endpoints
with gr.Blocks(title="AutoML Sandbox", theme=gr.themes.Soft()) as demo:
    gr.Markdown("# 🤖 AutoML Sandbox Runner")
    gr.Markdown(
        "✅ **Sandbox is online.**\n\n"
        "This is the backend execution engine for the **Agentic AutoML** platform."
    )
    
    # 1. Profile Endpoint
    file_input = gr.File(label="Upload Dataset", file_types=[".csv", ".xlsx"], visible=False)
    profile_output = gr.Textbox(label="Profile JSON String", visible=False)
    profile_btn = gr.Button("Profile", visible=False)
    profile_btn.click(fn=profile_dataset, inputs=file_input, outputs=profile_output, api_name="profile")
    
    # 2. Execute Endpoint
    script_input = gr.Textbox(label="Python Script", visible=False)
    timeout_input = gr.Number(value=60, label="Timeout", visible=False)
    execute_output = gr.Textbox(label="Execution Output String", visible=False)
    execute_btn = gr.Button("Execute", visible=False)
    execute_btn.click(
        fn=run_script_in_sandbox,
        inputs=[script_input, timeout_input],
        outputs=execute_output,
        api_name="execute"
    )

if __name__ == "__main__":
    demo.launch(server_name="0.0.0.0", server_port=7860, show_error=True)
