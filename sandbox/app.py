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

def profile_dataset(csv_content_str):
    """
    Ingests and profiles dataset using Pandas, returning schema and summary statistics.
    """
    if not csv_content_str:
        return json.dumps({"error": "No CSV content provided."})
        
    import io
    try:
        df = pd.read_csv(io.StringIO(csv_content_str))
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
    Executes the training script inside an isolated python subprocess in a temporary directory,
    zips up all generated model/code files in-memory, and returns stdout, stderr, exit_code,
    and a base64 encoded string of the ZIP archive.
    """
    import base64
    import zipfile
    import io
    
    # Create an isolated temporary directory for the execution
    with tempfile.TemporaryDirectory() as tmpdir:
        script_path = os.path.join(tmpdir, "model_training.py")
        with open(script_path, "w", encoding="utf-8") as f:
            f.write(script_content)
            
        try:
            # Execute in the temporary directory
            res = subprocess.run(
                [sys.executable, "model_training.py"],
                cwd=tmpdir,
                capture_output=True,
                text=True,
                timeout=timeout,
            )
            
            # Zip all generated files in the directory
            zip_buffer = io.BytesIO()
            with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
                for root, _, files in os.walk(tmpdir):
                    for file in files:
                        file_path = os.path.join(root, file)
                        # Archive relative to tmpdir
                        arcname = os.path.relpath(file_path, tmpdir)
                        zip_file.write(file_path, arcname)
                        
            zip_buffer.seek(0)
            zip_base64 = base64.b64encode(zip_buffer.read()).decode("utf-8")
            
            out = {
                "exit_code": res.returncode,
                "stdout": res.stdout,
                "stderr": res.stderr,
                "zip_base64": zip_base64
            }
            return json.dumps(out)
            
        except subprocess.TimeoutExpired:
            return json.dumps({"exit_code": -1, "stdout": "", "stderr": f"Timed out after {timeout}s.", "zip_base64": ""})
        except Exception as e:
            return json.dumps({"exit_code": -2, "stdout": "", "stderr": str(e), "zip_base64": ""})

# UI layout containing the API endpoints
with gr.Blocks(title="AutoML Sandbox", theme=gr.themes.Soft()) as demo:
    gr.Markdown("# 🤖 AutoML Sandbox Runner")
    gr.Markdown(
        "✅ **Sandbox is online.**\n\n"
        "This is the backend execution engine for the **Agentic AutoML** platform."
    )
    
    # 1. Profile Endpoint
    csv_input = gr.Textbox(label="CSV Content String", visible=False)
    profile_output = gr.Textbox(label="Profile JSON String", visible=False)
    profile_btn = gr.Button("Profile", visible=False)
    profile_btn.click(fn=profile_dataset, inputs=csv_input, outputs=profile_output, api_name="profile")
    
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
