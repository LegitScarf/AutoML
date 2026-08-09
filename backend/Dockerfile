FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend source code
COPY . /app/backend

# Expose FastAPI default port
EXPOSE 8000

# Set environment variable for python path
ENV PYTHONPATH=/app

# Start the uvicorn server, binding to all interfaces on port 8000 (standard for Render)
CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000"]
