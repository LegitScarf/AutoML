import os
import json
import pandas as pd
import pytest
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
    working_script = f"""
import joblib
from sklearn.linear_model import LogisticRegression
import numpy as np

# Mock training
X = np.array([[25, 50000], [30, 60000], [35, 70000], [40, 80000], [45, 90000]])
y = np.array([0, 0, 1, 1, 1])

model = LogisticRegression()
model.fit(X, y)

# Save
joblib.dump(model, "{model_path_safe}")
print("MODEL_SAVED_SUCCESS")
"""
    working_res_raw = execute_script_safely(working_script)
    working_res = json.loads(working_res_raw)
    
    assert working_res["exit_code"] == 0
    assert "MODEL_SAVED_SUCCESS" in working_res["stdout"]
    assert os.path.exists(model_path)
    
    # 3. Validate pipeline tool
    val_res_raw = validate_pipeline(str(model_path), preprocessor_path)
    val_res = json.loads(val_res_raw)
    assert val_res["exit_code"] == 0
    assert "VALIDATION_SUCCESS" in val_res["stdout"]
