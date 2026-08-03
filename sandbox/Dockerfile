FROM python:3.10-slim

# Set work directory
WORKDIR /workspace

# Install system dependencies if any are needed
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Install python dependencies for machine learning
RUN pip install --no-cache-dir \
    numpy \
    pandas \
    scikit-learn \
    xgboost \
    joblib \
    openpyxl

# Default command
CMD ["python"]
