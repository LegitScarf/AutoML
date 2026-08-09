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

import json

def profile_dataset(file_path):
    """
    Ingests and profiles dataset using Pandas, returning schema and summary statistics.
    """
    if not file_path:
        return json.dumps({"error": "No file uploaded."})
    
    if not file_path.endswith(('.csv', '.xlsx')):
        return json.dumps({"error": "Unsupported file format. Upload CSV or Excel."})
        
    try:
        if file_path.endswith('.csv'):
            df = pd.read_csv(file_path)
        else:
            df = pd.read_excel(file_path)
            
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
    demo.launch(server_name="0.0.0.0", server_port=7860)
