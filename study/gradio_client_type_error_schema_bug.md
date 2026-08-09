# Incident Report: Gradio Client Schema Parsing Bug

## 1. Incident Overview
During the execution of the AutoML pipeline, the backend orchestrator successfully ingested the dataset and attempted to connect to the Hugging Face Space runner. However, the pipeline crashed during the data profiling phase, throwing the following error trace:

```python
File "/usr/local/lib/python3.10/site-packages/gradio_client/utils.py", line 887, in get_type
  if "const" in schema:
TypeError: argument of type 'bool' is not iterable
```

---

## 2. Root Cause Analysis
The issue stems from a library bug within `gradio_client`'s type introspection engine during JSON schema decoding:

* **Endpoint Output:** The sandbox endpoints (`/profile` and `/execute`) were originally registered with `gr.JSON` output structures, returning native Python dictionaries.
* **Schema Introspection:** To allow remote orchestration, `gradio_client` queries the Space's `/info` route to fetch the JSON schema of each endpoint.
* **Boolean Mismatch:** Under newer Pydantic versions, the generated JSON schema represents dictionary keys as `"additionalProperties": true`.
* **The Crash:** The `gradio_client` utility parser maps these properties recursively. It processes `schema['additionalProperties']` which returns the boolean `True`, and passes it to the `get_type(schema)` function. Inside `get_type`, it executes `if "const" in schema:`. Since a boolean is not iterable or subscriptable, Python raises a `TypeError`.

---

## 3. Implementation Solution
Rather than pinning complex dependencies (which can break when cloud containers update or rebuild), we implemented a protocol-level workaround to bypass Gradio's JSON schema type checker entirely.

### Step 1: Sandbox Protocol Conversion
We modified [`sandbox/app.py`](file:///c:/Users/KIIT/Desktop/AutoML/sandbox/app.py):
* Swapped the output interface from `gr.JSON` to **`gr.Textbox`**.
* The python functions `profile_dataset` and `run_script_in_sandbox` now return flat JSON-serialized strings using `json.dumps(res)`. 
* **Why this works:** The schema of a string textbox is simple (`{ "type": "string" }`) and lacks nested properties, preventing `gradio_client` from executing the buggy `additionalProperties` loop.

### Step 2: Backend Orchestrator Parsing
We modified [`backend/orchestrator.py`](file:///c:/Users/KIIT/Desktop/AutoML/backend/orchestrator.py):
* Added type-safety guards to intercepts incoming responses.
* If a response is received as a string, it automatically parses it using `json.loads(res)` before carrying out any key access operations:
  ```python
  if isinstance(profile_res, str):
      profile_res = json.loads(profile_res)
  ```

---

## 4. Deployment Status
Both updates were successfully pushed to production:
* **Hugging Face Sandbox Repo:** Pushed to `main` branch.
* **Main AutoML Repo:** Pushed to `prod` branch on GitHub.
