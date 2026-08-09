import os
import json
import pandas as pd
import pytest
import joblib
from sklearn.linear_model import LogisticRegression
from mcp_servers.profiler_server import profile_dataset, get_sample_rows
from mcp_servers.sandbox_server import execute_script_safely, validate_pipeline

@pytest.fixture
def sample_dataset(tmp_path):
    """Creates a simple mock dataset for testing."""
    data = {
        "age": [25, 30, 35, 40, 45],
        "salary": [50000, 60000, 70000, 80000, 90000],
        "purchased": [0, 0, 1, 1, 1]
    }
    df = pd.DataFrame(data)
    file_path = tmp_path / "mock_data.csv"
    df.to_csv(file_path, index=False)
    return str(file_path)

def test_data_profiler(sample_dataset):
    """Tests the profile_dataset and get_sample_rows tools."""
    profile_res = profile_dataset(sample_dataset)
    profile_data = json.loads(profile_res)
    
    assert "error" not in profile_data
    assert profile_data["num_rows"] == 5
    assert profile_data["num_cols"] == 3
    assert "age" in profile_data["numeric_columns"]
    
    sample_res = get_sample_rows(sample_dataset, n=2)
    sample_data = json.loads(sample_res)
    assert len(sample_data) == 2

def test_sandbox_self_correction_loop(tmp_path):
    """Tests executing script in sandbox, catching error, correcting, and validating."""
    model_path = tmp_path / "model.pkl"
    preprocessor_path = "" # None for simple model
    
    # 1. Script with a syntax/import error
    buggy_script = f"""
import joblib
import missing_package_name_error
"""
    buggy_res_raw = execute_script_safely(buggy_script)
    buggy_res = json.loads(buggy_res_raw)
    
    assert buggy_res["exit_code"] != 0
    assert "ModuleNotFoundError" in buggy_res["stderr"]
    
    # 2. Corrected training script
    model_path_safe = str(model_path).replace("\\", "/")
    preprocessor_path_safe = model_path_safe.replace("model.pkl", "preprocessor.pkl")
    reqs_path_safe = model_path_safe.replace("model.pkl", "requirements.txt")
    inf_path_safe = model_path_safe.replace("model.pkl", "inference.py")
    rep_path_safe = model_path_safe.replace("model.pkl", "training_report.pdf")
    
    working_script = f"""
import joblib
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler
import numpy as np
import os
from reportlab.platypus import SimpleDocTemplate, Paragraph
from reportlab.lib.styles import getSampleStyleSheet

# Resolve output path dynamically
out_dir = "/workspace/host_dir" if os.path.exists("/workspace/host_dir") else "."
model_path = os.path.join(out_dir, "test_model.pkl")
prep_path = os.path.join(out_dir, "test_preprocessor.pkl")
reqs_path = os.path.join(out_dir, "test_requirements.txt")
inf_path = os.path.join(out_dir, "test_inference.py")
rep_path = os.path.join(out_dir, "test_training_report.pdf")

# Mock training
X = np.array([[25, 50000], [30, 60000], [35, 70000], [40, 80000], [45, 90000]])
y = np.array([0, 0, 1, 1, 1])

scaler = StandardScaler()
X_scaled = scaler.fit_transform(X)

model = LogisticRegression()
model.fit(X_scaled, y)

# Save artifacts
joblib.dump(model, model_path)
joblib.dump(scaler, prep_path)

with open(reqs_path, "w") as f:
    f.write("scikit-learn\\npandas\\nnumpy\\njoblib\\nmatplotlib\\nreportlab\\n")

with open(inf_path, "w") as f:
    f.write("def predict(data): return 1\\n")

# Create simple PDF
doc = SimpleDocTemplate(rep_path)
styles = getSampleStyleSheet()
story = [Paragraph("AutoML Model Training Report", styles['Title'])]
doc.build(story)

print("MODEL_SAVED_SUCCESS")
"""
    working_res_raw = execute_script_safely(working_script)
    working_res = json.loads(working_res_raw)
    
    assert working_res["exit_code"] == 0
    assert "MODEL_SAVED_SUCCESS" in working_res["stdout"]
    
    # Assert existence on host side
    assert os.path.exists("test_model.pkl")
    assert os.path.exists("test_preprocessor.pkl")
    assert os.path.exists("test_requirements.txt")
    assert os.path.exists("test_inference.py")
    assert os.path.exists("test_training_report.pdf")
    
    # Clean up test output files
    for f in ["test_model.pkl", "test_preprocessor.pkl", "test_requirements.txt", "test_inference.py", "test_training_report.pdf"]:
        if os.path.exists(f):
            os.remove(f)
            
    # 3. Validate pipeline tool
    # Use standard local paths for validation test
    mock_model = "test_model_val.pkl"
    joblib.dump(LogisticRegression(), mock_model)
    val_res_raw = validate_pipeline(mock_model, "")
    val_res = json.loads(val_res_raw)
    if os.path.exists(mock_model):
        os.remove(mock_model)
    assert val_res["exit_code"] == 0
    assert "VALIDATION_SUCCESS" in val_res["stdout"]
