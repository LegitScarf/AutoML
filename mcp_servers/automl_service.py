import os
import json
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional
import uvicorn

# Import logic directly from our existing MCP servers
from mcp_servers.profiler_server import profile_dataset as run_profile, get_sample_rows as run_sample
from mcp_servers.sandbox_server import execute_script_safely as run_execute, validate_pipeline as run_validate

app = FastAPI(title="AutoML Unified Service", description="Exposes both standard REST endpoints for n8n and MCP tools.")

# Pydantic request models
class FilePathRequest(BaseModel):
    file_path: str

class SampleRowsRequest(BaseModel):
    file_path: str
    n: Optional[int] = 5

class ExecuteRequest(BaseModel):
    script_content: str
    timeout: Optional[int] = 60

class ValidateRequest(BaseModel):
    model_path: str
    preprocessor_path: Optional[str] = ""

import zipfile

# REST API Endpoints
@app.post("/profile_dataset")
def profile_dataset_endpoint(req: FilePathRequest):
    res = run_profile(req.file_path)
    try:
        data = json.loads(res)
        if "error" in data:
            raise HTTPException(status_code=400, detail=data["error"])
        return data
    except json.JSONDecodeError:
        return {"output": res}

@app.post("/get_sample_rows")
def get_sample_rows_endpoint(req: SampleRowsRequest):
    res = run_sample(req.file_path, req.n)
    try:
        data = json.loads(res)
        if "error" in data:
            raise HTTPException(status_code=400, detail=data["error"])
        return data
    except json.JSONDecodeError:
        return {"output": res}

@app.post("/execute_script_safely")
def execute_script_safely_endpoint(req: ExecuteRequest):
    res = run_execute(req.script_content, req.timeout)
    try:
        return json.loads(res)
    except json.JSONDecodeError:
        return {"output": res}

@app.post("/validate_pipeline")
def validate_pipeline_endpoint(req: ValidateRequest):
    res = run_validate(req.model_path, req.preprocessor_path)
    try:
        data = json.loads(res)
        if data.get("exit_code") == 0:
            # Create a zip package of the output files
            zip_path = "automl_bundle.zip"
            files_to_zip = ["model.pkl", "preprocessor.pkl", "inference.py"]
            with zipfile.ZipFile(zip_path, 'w') as zipf:
                for file in files_to_zip:
                    # Check if file exists in current dir or temp dir
                    if os.path.exists(file):
                        zipf.write(file)
                    elif os.path.exists(os.path.join(os.path.dirname(req.model_path), file)):
                        zipf.write(os.path.join(os.path.dirname(req.model_path), file), arcname=file)
            data["download_url"] = "http://host.docker.internal:8000/download_bundle"
        return data
    except json.JSONDecodeError:
        return {"output": res}

@app.get("/download_bundle")
def download_bundle():
    zip_path = "automl_bundle.zip"
    if os.path.exists(zip_path):
        from fastapi.responses import FileResponse
        return FileResponse(zip_path, media_type="application/zip", filename="automl_bundle.zip")
    raise HTTPException(status_code=404, detail="Bundle file not found. Run validation first.")

# Healthcheck
@app.get("/health")
def health():
    return {"status": "healthy"}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
