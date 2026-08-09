# Architectural Study & Fix Plan: Hugging Face Sandbox Runtime Error (Exit Code: 0)

## 1. Architectural Study of the Root Cause

The screenshot shows a **Runtime error** with **Exit code: 0** and empty container logs after the initialization message:
`===== Application Startup at 2026-08-08 19:17:41 =====`

### Why Exit Code 0 Occurs
In a Hugging Face Space using the Gradio SDK, the platform launches the container and executes your entry point file via `python app.py`.
* In our updated [`app.py`](file:///c:/Users/KIIT/Desktop/AutoML/sandbox/app.py), the script imports modules, defines the FastAPI app, builds the Gradio block structure, and calls `gr.mount_gradio_app(...)`.
* **The Missing Step:** After mounting the Gradio app, the script has no further statements. It simply finishes executing the code and exits.
* Because the Python process finished all instructions successfully, it exited with a **clean exit code of 0**.
* Hugging Face detects that the container's main web process has stopped running, causing the container to shut down and flag a `Runtime error` (since a web server process is expected to run indefinitely).

---

## 2. Implementation Plan to Solve It Permanently

To keep the container running indefinitely, we must explicitly start a blocking web server (Uvicorn) at the end of the script to serve the mounted application.

### Proposed Changes

#### [MODIFY] [app.py](file:///c:/Users/KIIT/Desktop/AutoML/sandbox/app.py)

We will append a standard Python execution guard at the bottom of the script to launch `uvicorn` on port `7860` (the default port Hugging Face forwards for Spaces) and host `0.0.0.0`.

We will replace the final lines of [`app.py`](file:///c:/Users/KIIT/Desktop/AutoML/sandbox/app.py):

```python
# Mount the FastAPI sub-app into Gradio's internal ASGI app so all
# /profile and /execute routes are reachable alongside the Gradio UI.
app = gr.mount_gradio_app(api, demo, path="/ui")
```

With:

```python
# Mount the FastAPI sub-app into Gradio's internal ASGI app so all
# /profile and /execute routes are reachable alongside the Gradio UI.
app = gr.mount_gradio_app(api, demo, path="/ui")

if __name__ == "__main__":
    import uvicorn
    # Hugging Face runs the app by executing `python app.py`. 
    # This block keeps the server running indefinitely on port 7860.
    uvicorn.run(app, host="0.0.0.0", port=7860)
```

---

## 3. Verification Plan

### Local Verification
1. Run the script locally:
   ```bash
   cd sandbox
   .venv\Scripts\python app.py
   ```
2. Verify that the process **blocks** and does not exit immediately.
3. Access `http://localhost:7860/health` in your browser and check if it returns `{"status": "Sandbox online"}`.

### Hugging Face Verification
1. Commit the change to the `sandbox` git repository and push it to Hugging Face.
2. Confirm the Hugging Face console shows the server log and transitions to a green **Running** status.
