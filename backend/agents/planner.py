import json
from .config import get_openai_client, OPENAI_MODEL

def ask_planner_agent(model_name: str, task: str, target: str, profile_res: dict) -> str:
    """
    Queries OpenAI gpt-5.6-luna to generate a comprehensive statistical machine learning plan
    customized to the dataset, target variable, task type, and model choice.
    """
    client = get_openai_client()
    
    # Extract profile attributes to explain to the agent
    num_rows = profile_res.get("num_rows", 0)
    num_cols = profile_res.get("num_cols", 0)
    dtypes = profile_res.get("dtypes", {})
    missing = profile_res.get("missing_counts", {})
    numeric_cols = profile_res.get("numeric_columns", [])
    categorical_cols = profile_res.get("categorical_columns", [])
    
    prompt = f"""You are a world-class Data Science Planner Agent. Your job is to create a step-by-step statistical plan for training a machine learning model.
Analyze the following dataset profile and user configuration:

## User Configuration:
* **Selected Model:** {model_name}
* **Task Type:** {task}
* **Target Variable:** {target}

## Dataset Profile:
* **Dimensions:** {num_rows} rows, {num_cols} columns
* **Feature Column Data Types:** {json.dumps(dtypes)}
* **Missing Value Counts:** {json.dumps(missing)}
* **Numeric Columns:** {json.dumps(numeric_cols)}
* **Categorical Columns:** {json.dumps(categorical_cols)}

## Your Task:
Create a detailed, numbered markdown checklist plan for building this model.
Include specific data science procedures:
1. Handling missing values (imputation strategies for both numeric and categorical columns).
2. Scaling and categorical encoding details (StandardScaler, OneHotEncoder).
3. If the model is a linear model (Linear Regression, Logistic Regression), plan a multicollinearity check using Variance Inflation Factor (VIF > 5.0) and specify dropping redundant features.
4. Splitting the data into train/validation sets (e.g., 80/20 train/test split).
5. Model training, predictions, and evaluation metrics (Accuracy, F1-Score for classification, or R2, MAE, RMSE for regression).
6. Plotting diagnostics (saving confusion matrix or residuals distribution as PNG files).
7. Feature importance or coefficient weights visualization plotting.
8. Saving the model (model.pkl) and preprocessor transformer (preprocessor.pkl) to disk.

Output ONLY the clear, structured Markdown document. Do not wrap it in code blocks or include extra preamble.
"""
    
    response = client.chat.completions.create(
        model=OPENAI_MODEL,
        messages=[
            {"role": "system", "content": "You are a precise, senior data scientist that outputs markdown execution plans."},
            {"role": "user", "content": prompt}
        ]
    )
    
    return response.choices[0].message.content.strip()
