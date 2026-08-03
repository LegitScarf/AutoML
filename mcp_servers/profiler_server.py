import os
import json
import pandas as pd
from fastmcp import FastMCP

mcp = FastMCP("Data Profiler")

@mcp.tool()
def profile_dataset(file_path: str) -> str:
    """
    Analyzes a CSV or Excel dataset and returns schema, shape, missing values,
    data types, and target variable distribution.
    """
    if not os.path.exists(file_path):
        return json.dumps({"error": f"File not found: {file_path}"})
    
    try:
        # Determine file type and load
        if file_path.endswith('.csv'):
            df = pd.read_csv(file_path)
        elif file_path.endswith(('.xls', '.xlsx')):
            df = pd.read_excel(file_path)
        else:
            return json.dumps({"error": "Unsupported file format. Please upload CSV or Excel."})
        
        # Gather basic stats
        shape = df.shape
        dtypes = {col: str(dtype) for col, dtype in df.dtypes.items()}
        missing_values = df.isnull().sum().to_dict()
        num_columns = list(df.select_dtypes(include='number').columns)
        cat_columns = list(df.select_dtypes(exclude='number').columns)
        
        summary = {
            "num_rows": shape[0],
            "num_cols": shape[1],
            "dtypes": dtypes,
            "missing_counts": missing_values,
            "numeric_columns": num_columns,
            "categorical_columns": cat_columns,
        }
        
        return json.dumps(summary, indent=2)
        
    except Exception as e:
        return json.dumps({"error": f"Failed to profile dataset: {str(e)}"})

@mcp.tool()
def get_sample_rows(file_path: str, n: int = 5) -> str:
    """
    Returns the first n rows of a dataset to help the agent understand the values.
    """
    if not os.path.exists(file_path):
        return json.dumps({"error": f"File not found: {file_path}"})
    
    try:
        if file_path.endswith('.csv'):
            df = pd.read_csv(file_path, nrows=n)
        elif file_path.endswith(('.xls', '.xlsx')):
            df = pd.read_excel(file_path, nrows=n)
        else:
            return json.dumps({"error": "Unsupported file format."})
            
        return df.to_json(orient='records', indent=2)
    except Exception as e:
        return json.dumps({"error": f"Failed to read sample rows: {str(e)}"})

if __name__ == "__main__":
    mcp.run()
