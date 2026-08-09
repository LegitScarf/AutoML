import os
from pathlib import Path

import joblib
import numpy as np
import pandas as pd

FEATURE_COLUMNS = ['src_bytes', 'dst_bytes', 'packet_count', 'protocol', 'failed_logins', 'attack_type']


def predict(data):
    base_dir = Path(__file__).resolve().parent
    model = joblib.load(base_dir / "model.pkl")
    preprocessor = joblib.load(base_dir / "preprocessor.pkl")

    if isinstance(data, pd.DataFrame):
        frame = data.copy()
    elif isinstance(data, dict):
        if any(isinstance(value, (list, tuple, np.ndarray, pd.Series)) for value in data.values()):
            frame = pd.DataFrame(data)
        else:
            frame = pd.DataFrame([data])
    else:
        array = np.asarray(data)
        if array.ndim == 1:
            array = array.reshape(1, -1)
        frame = pd.DataFrame(array, columns=FEATURE_COLUMNS)

    if "duration" in frame.columns:
        frame = frame.drop(columns=["duration"])

    missing_columns = [column for column in FEATURE_COLUMNS if column not in frame.columns]
    for column in missing_columns:
        frame[column] = np.nan

    frame = frame[FEATURE_COLUMNS]
    transformed = preprocessor.transform(frame)
    return model.predict(transformed)
