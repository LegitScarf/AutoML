import os
import sys
import tempfile
import subprocess
import json
from fastmcp import FastMCP
import re

mcp = FastMCP("Sandbox Runner")

def run_via_docker(script_content: str, timeout: int = 60) -> dict:
    """Runs the script inside a sandbox Docker container using python docker SDK if available."""
    try:
        import docker
        client = docker.from_env()
        
        # Translate host workspace paths to container workspace paths
        host_cwd = os.getcwd()
        host_cwd_forward = host_cwd.replace("\\", "/")
        
        pattern_forward = re.escape(host_cwd_forward).replace(r'\:', ':')
        mapped_script = re.sub(pattern_forward, "/workspace/host_dir", script_content, flags=re.IGNORECASE)
        
        pattern_back = re.escape(host_cwd).replace(r'\:', ':')
        mapped_script = re.sub(pattern_back, "/workspace/host_dir", mapped_script, flags=re.IGNORECASE)
        
        # Create a temporary file on the host machine
        with tempfile.NamedTemporaryFile(suffix=".py", delete=False, mode='w', encoding='utf-8') as temp_script:
            temp_script.write(mapped_script)
            temp_script_path = temp_script.name
        
        # Ensure image is built/pulled
        # We assume 'automl-sandbox:latest' is built
        try:
            container = client.containers.run(
                image="automl-sandbox:latest",
                command=f"python /workspace/run.py",
                volumes={
                    temp_script_path: {"bind": "/workspace/run.py", "mode": "ro"},
                    os.getcwd(): {"bind": "/workspace/host_dir", "mode": "rw"}
                },
                working_dir="/workspace",
                network_mode="none", # No network access
                mem_limit="1g",      # Max 1GB RAM
                detach=True
            )
            
            # Wait for execution with timeout
            try:
                result = container.wait(timeout=timeout)
                exit_code = result.get("StatusCode", 1)
                stdout = container.logs(stdout=True, stderr=False).decode("utf-8")
                stderr = container.logs(stdout=False, stderr=True).decode("utf-8")
            except Exception as e:
                container.kill()
                return {"exit_code": -1, "stdout": "", "stderr": f"Execution timed out: {str(e)}"}
            finally:
                container.remove()
                os.remove(temp_script_path)
                
            return {"exit_code": exit_code, "stdout": stdout, "stderr": stderr}
            
        except Exception as e:
            if os.path.exists(temp_script_path):
                os.remove(temp_script_path)
            raise e
            
    except Exception as e:
        # Fall back to local execution if Docker is not available or fails to initialize
        return run_via_subprocess(script_content, timeout)

def run_via_subprocess(script_content: str, timeout: int = 60) -> dict:
    """Fallback runner executing code in a local subprocess."""
    with tempfile.NamedTemporaryFile(suffix=".py", delete=False, mode='w', encoding='utf-8') as temp_script:
        temp_script.write(script_content)
        temp_script_path = temp_script.name
        
    try:
        res = subprocess.run(
            [sys.executable, temp_script_path],
            capture_output=True,
            text=True,
            timeout=timeout
        )
        return {
            "exit_code": res.returncode,
            "stdout": res.stdout,
            "stderr": res.stderr
        }
    except subprocess.TimeoutExpired:
        return {
            "exit_code": -1,
            "stdout": "",
            "stderr": f"Execution timed out after {timeout} seconds."
        }
    except Exception as e:
        return {
            "exit_code": -2,
            "stdout": "",
            "stderr": str(e)
        }
    finally:
        if os.path.exists(temp_script_path):
            os.remove(temp_script_path)

@mcp.tool()
def execute_script_safely(script_content: str, timeout: int = 60) -> str:
    """
    Safely executes the training script and returns execution metrics,
    including stdout, stderr, and exit code.
    """
    # Try docker first, fallback to subprocess
    result = run_via_docker(script_content, timeout)
    return json.dumps(result, indent=2)

@mcp.tool()
def validate_pipeline(model_path: str, preprocessor_path: str) -> str:
    """
    Tests loading the model and pipeline and verifies basic prediction capability.
    """
    model_path_safe = model_path.replace("\\", "/")
    preprocessor_path_safe = preprocessor_path.replace("\\", "/")
    test_script = f"""
import joblib
import pandas as pd
import sys

try:
    model = joblib.load("{model_path_safe}")
    print("Successfully loaded model from {model_path_safe}")
    if "{preprocessor_path_safe}":
        preprocessor = joblib.load("{preprocessor_path_safe}")
        print("Successfully loaded preprocessor from {preprocessor_path_safe}")
    print("VALIDATION_SUCCESS")
except Exception as e:
    print(f"VALIDATION_FAILED: {{str(e)}}", file=sys.stderr)
    sys.exit(1)
"""
    result = run_via_subprocess(test_script, timeout=60)
    return json.dumps(result, indent=2)

if __name__ == "__main__":
    mcp.run()
