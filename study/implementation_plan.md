# Implementation Plan - Agentic AutoML Core Engine

This plan outlines the steps to build the core execution engine of the AutoML platform. We will implement the isolated Docker sandbox, the two Model Context Protocol (MCP) servers (Data Profiling and Sandbox Execution), the orchestrating n8n workflow, and verify the self-correction training loop.

## Proposed Changes

### [Component 1] Execution Sandbox (Docker)
We need an isolated container environment containing common ML/DL packages to execute generated scripts safely.

#### [NEW] [Dockerfile](file:///c:/Users/KIIT/Desktop/AutoML/sandbox/Dockerfile)
* Docker image with Python, `scikit-learn`, `pandas`, `numpy`, `xgboost`, and `joblib`.
* Network access disabled during container run.

---

### [Component 2] MCP Servers
We will create Python-based MCP servers using the `mcp` SDK to expose tools to our agents.

#### [NEW] [profiler_server.py](file:///c:/Users/KIIT/Desktop/AutoML/mcp_servers/profiler_server.py)
* **Tools:**
  * `profile_dataset(file_path)`: Uses `pandas` to inspect shape, null values, columns, and target distribution. Returns metadata as a JSON string.
  * `get_sample_rows(file_path, n=5)`: Safely parses and returns top rows.

#### [NEW] [sandbox_server.py](file:///c:/Users/KIIT/Desktop/AutoML/mcp_servers/sandbox_server.py)
* **Tools:**
  * `execute_script_safely(script_content)`: Writes `script_content` to a temporary file, mounts it inside the sandbox Docker container, runs it, and returns `stdout`, `stderr`, and exit code.
  * `validate_pipeline(model_path, preprocessor_path)`: Runs a sanity check ensuring inference functions correctly on mock inputs.

---

### [Component 3] n8n Workflow Orchestrator
We need to set up the orchestration graph that loops and handles self-correction using the MCP servers.

#### [NEW] [automl_workflow.json](file:///c:/Users/KIIT/Desktop/AutoML/n8n/automl_workflow.json)
* n8n Workflow definition containing:
  * An HTTP Webhook trigger accepting a CSV file path.
  * Node to call the Data Profiler MCP tools.
  * An AI Agent Node (configured with an LLM and our Sandbox/Profiler MCP tools) that writes and tests the training script.
  * A conditional loop node to handle automatic code execution retry if the Sandbox returns a non-zero exit code.
  * A file output node packaging the training report, `model.pkl`, and inference scripts into a ZIP.

---

### [Component 4] Verification Tests

#### [NEW] [test_core_pipeline.py](file:///c:/Users/KIIT/Desktop/AutoML/tests/test_core_pipeline.py)
* Integration test that calls the MCP tools sequentially:
  1. Profiles a mock dataset.
  2. Runs a script containing a syntax error/bug, verifying the error traceback is correctly captured and returned.
  3. Corrects the script and runs it again, verifying the generation of `model.pkl`.

## Verification Plan

### Automated Tests
* Run the integration test suite:
  ```bash
  pytest tests/test_core_pipeline.py
  ```

### Manual Verification
* Inspect the output folder for `model.pkl`, `preprocessor.pkl`, and `inference.py` after a successful run.
