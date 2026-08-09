---
title: AutoML Sandbox
emoji: 🤖
colorFrom: indigo
colorTo: purple
sdk: gradio
sdk_version: "5.9.1"
app_file: app.py
pinned: false
---

# AutoML Sandbox Runner

A secure execution sandbox for the Agentic AutoML platform. Exposes REST API endpoints for dataset profiling and isolated Python script execution.

## API Endpoints

- `GET /` — Health check
- `POST /profile` — Upload a CSV/Excel file and get a schema + summary profile
- `POST /execute` — Submit a Python training script and receive stdout/stderr logs
