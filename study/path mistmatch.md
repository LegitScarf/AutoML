# Goal Description

Resolve the path translation failure where the training script execution inside the sandbox fails with `FileNotFoundError` because of a case-sensitivity mismatch (e.g. `c:/Users/...` vs `C:/Users/...`) between the host path passed by Streamlit/Webhook and the `os.getcwd()` casing.

## Architectural Study & Research Findings

### 1. The Root Cause of the Casing Mismatch
* Streamlit uploads/saves files to a path starting with `c:/Users/...` (lowercase `c`).
* The unified service's `os.getcwd()` on the host returns `C:\Users\...` (uppercase `C`).
* The `.replace(host_cwd, ...)` path translation in `sandbox_server.py` is case-sensitive. Because `"c:/"` does not match `"C:/"`, the string replacement is skipped.
* As a result, the training script running inside the Docker sandbox tries to open `c:/Users/KIIT/Desktop/AutoML/uploaded_dataset.csv`. Because the isolated Docker container has no `c:` drive mounted, it crashes with `FileNotFoundError`.

### 2. The Solution
We need a case-insensitive path replacement logic. In Python, we can achieve this robustly using regular expressions (`re.sub` with `re.IGNORECASE`) to translate any occurrences of the workspace folder path into `/workspace/host_dir` regardless of whether they start with `c:` or `C:` (or any other casing differences in the path).

---

## Proposed Changes

### [Component 1] Sandbox Path Translation

#### [MODIFY] [sandbox_server.py](file:///c:/Users/KIIT/Desktop/AutoML/mcp_servers/sandbox_server.py)
* Refactor the string-replace path mapping inside `run_via_docker` to use a case-insensitive regex substitution.
* E.g.:
  ```python
  import re
  # Match host path case-insensitively and replace with container path
  pattern = re.escape(host_cwd_forward).replace(r'\:', ':') # Escape regex
  mapped_script = re.sub(pattern, "/workspace/host_dir", script_content, flags=re.IGNORECASE)
  
  # Also handle backslash versions
  pattern_back = re.escape(host_cwd).replace(r'\:', ':')
  mapped_script = re.sub(pattern_back, "/workspace/host_dir", mapped_script, flags=re.IGNORECASE)
  ```

---

## Verification Plan

### Manual Verification
1. Approve and apply the changes.
2. Run a test pipeline from the Streamlit UI with both local path/uploaded CSV to verify it successfully translates the path, executes, validates, and packages all 5 files.
