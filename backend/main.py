import os
import tempfile
from dotenv import load_dotenv

# Load env configurations from local .env file
load_dotenv()

from fastapi import FastAPI, UploadFile, File, Form, Depends, BackgroundTasks, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from typing import List

from .db.database import get_db
from .models import AutoMLRun
from .orchestrator import run_automl_pipeline
from .auth import get_current_user_id

app = FastAPI(title="AutoML Backend Orchestrator", version="0.1.0")

from fastapi.staticfiles import StaticFiles
# Ensure static directory exists for bundle downloads
os.makedirs("static/bundles", exist_ok=True)
app.mount("/static", StaticFiles(directory="static"), name="static")

# Automatic startup schema migration patch (adds 'plan' and 'user_id' columns if missing)
try:
    from sqlalchemy import text, inspect
    from .db.database import engine
    
    # Check columns using metadata inspection to prevent transaction failures in Postgres
    inspector = inspect(engine)
    columns = [col['name'] for col in inspector.get_columns("runs")]
    
    if "plan" not in columns:
        with engine.begin() as conn:
            if engine.url.drivername.startswith("sqlite"):
                conn.execute(text("ALTER TABLE runs ADD COLUMN plan TEXT;"))
            else:
                conn.execute(text("ALTER TABLE runs ADD COLUMN IF NOT EXISTS plan TEXT;"))
            print("Startup migration: plan column added successfully.")
            
    if "user_id" not in columns:
        with engine.begin() as conn:
            if engine.url.drivername.startswith("sqlite"):
                conn.execute(text("ALTER TABLE runs ADD COLUMN user_id VARCHAR(100);"))
            else:
                conn.execute(text("ALTER TABLE runs ADD COLUMN IF NOT EXISTS user_id VARCHAR(100);"))
            print("Startup migration: user_id column added successfully.")
except Exception as e:
    print(f"Startup migration patch skipped/completed: {str(e)}")


# Enable CORS for Vercel Frontend and local dev
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # In production, restrict to Vercel domains
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def read_root():
    return {"message": "AutoML Agentic Core API online"}

@app.post("/api/upload")
async def upload_dataset(
    file: UploadFile = File(...),
    target_variable: str = Form("purchased"),
    task_type: str = Form("classification"),
    selected_model: str = Form("Logistic Regression"),
    min_threshold: float = Form(0.90),
    db: Session = Depends(get_db),
    current_user_id: str = Depends(get_current_user_id)
):
    """
    Receives dataset file, saves metadata in database, and schedules upload to storage.
    """
    if not file.filename.endswith(('.csv', '.xlsx')):
        raise HTTPException(status_code=400, detail="Unsupported file format. Upload CSV or Excel.")

    # Read content to forward to orchestrator
    content = await file.read()
    
    # Save a run record in DB
    run = AutoMLRun(
        dataset_name=file.filename,
        target_variable=target_variable,
        task_type=task_type,
        selected_model=selected_model,
        min_threshold=min_threshold,
        status="pending",
        user_id=current_user_id,
        logs=["[SYSTEM] Run initialized. Ready for execution."]
    )
    db.add(run)
    db.commit()
    db.refresh(run)

    # Save uploaded file bytes to a temp file tagged by run ID
    temp_file_path = os.path.join(tempfile.gettempdir(), f"{run.id}_{file.filename}")
    try:
        with open(temp_file_path, "wb") as f:
            f.write(content)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to buffer dataset on server disk: {str(e)}")

    return {
        "run_id": run.id,
        "dataset_name": run.dataset_name,
        "status": run.status,
        "message": "Dataset uploaded and run initialized successfully."
    }

@app.post("/api/runs/{run_id}/trigger")
def trigger_pipeline(
    run_id: str,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user_id: str = Depends(get_current_user_id)
):
    """
    Triggers the AutoML pipeline asynchronously in the background.
    """
    run = db.query(AutoMLRun).filter(AutoMLRun.id == run_id, AutoMLRun.user_id == current_user_id).first()
    if not run:
        raise HTTPException(status_code=404, detail="AutoML Run not found or access denied.")
        
    if run.status != "pending":
        raise HTTPException(status_code=400, detail=f"Run has already been triggered. Status: {run.status}")

    # Retrieve stored temp file content
    temp_file_path = os.path.join(tempfile.gettempdir(), f"{run.id}_{run.dataset_name}")
    file_content = b""
    if os.path.exists(temp_file_path):
        try:
            with open(temp_file_path, "rb") as f:
                file_content = f.read()
        except Exception:
            pass

    # Launch background job
    background_tasks.add_task(
        run_automl_pipeline,
        run_id=run.id,
        file_content=file_content,
        filename=run.dataset_name,
        db=db
    )
    
    # Clean up temp file from disk now that bytes are loaded into the worker task
    try:
        if os.path.exists(temp_file_path):
            os.remove(temp_file_path)
    except Exception:
        pass
    
    run.status = "uploading"
    db.commit()

    return {"message": "AutoML pipeline execution triggered in the background."}

@app.get("/api/runs")
def get_all_runs(
    db: Session = Depends(get_db),
    current_user_id: str = Depends(get_current_user_id)
):
    """
    Returns list of all historical AutoML training runs for the current user.
    """
    runs = db.query(AutoMLRun).filter(AutoMLRun.user_id == current_user_id).order_by(AutoMLRun.created_at.desc()).all()
    return runs

@app.get("/api/runs/{run_id}/status")
def get_run_status(
    run_id: str,
    db: Session = Depends(get_db),
    current_user_id: str = Depends(get_current_user_id)
):
    """
    Retrieves execution logs, progress status, and final accuracy metrics.
    """
    run = db.query(AutoMLRun).filter(AutoMLRun.id == run_id, AutoMLRun.user_id == current_user_id).first()
    if not run:
        raise HTTPException(status_code=404, detail="Run not found or access denied.")
        
    return {
        "run_id": run.id,
        "status": run.status,
        "metrics": run.metrics,
        "logs": run.logs,
        "plan": run.plan,
        "bundle_url": run.bundle_url,
        "created_at": run.created_at
    }
