# Architectural Study & Fix Plan: Rooting Out the ZeroGPU "No @spaces.GPU function detected" Issue

This document presents a deep-dive architectural study of why the Hugging Face ZeroGPU parser fails when spaces imports are nested, and provides a permanent fix that maintains local dev compatibility.

---

## 1. Architectural Study of the Root Cause

Even though we added an invisible Gradio button click handler, the space still crashed during startup with:
`No @spaces.GPU function detected during startup`

### How Hugging Face ZeroGPU Detects the Decorator
Hugging Face's ZeroGPU infrastructure validates every Gradio space *before* running it. It does this using a **static code parser** (similar to Python's built-in `ast` module) to scan the repository for GPU declarations.

To save resources and compile quickly, the static parser runs a strict AST match. It looks for:
1. A **top-level** import statement (i.e. `import spaces` at the root body of the module).
2. The decorator `@spaces.GPU` applied to a module-level function.

### The Parsing Bug in our Previous Implementation
In our previous code, the import was nested inside a `try/except` block:
```python
try:
    import spaces
except ImportError:
    class spaces:
        ...
```

For a static AST parser looking for top-level nodes, `import spaces` was located inside an `ast.Try` node rather than the root `ast.Module` body. The parser only scanned the root level imports, failed to match `import spaces`, and concluded that the application did not use any GPU functions.

---

## 2. Permanent Fix Plan

We will restructure [`sandbox/app.py`](file:///c:/Users/KIIT/Desktop/AutoML/sandbox/app.py) to declare `import spaces` as a **top-level, unindented statement** to satisfy the static AST scanner. 

To keep local execution from crashing due to `ModuleNotFoundError`, we will inject our mock `spaces` module into Python's global module registry (`sys.modules`) *before* the top-level import is evaluated.

### Proposed Code Changes

#### [MODIFY] [sandbox/app.py](file:///c:/Users/KIIT/Desktop/AutoML/sandbox/app.py)

We will modify the top of [`sandbox/app.py`](file:///c:/Users/KIIT/Desktop/AutoML/sandbox/app.py) to look as follows:

```python
import sys
import types

# 1. Inject a mock 'spaces' module into sys.modules if not installed (for local environments)
try:
    import spaces
except ImportError:
    mock_spaces = types.ModuleType("spaces")
    mock_spaces.GPU = lambda func: func
    sys.modules["spaces"] = mock_spaces

# 2. Top-level, unindented import for Hugging Face's static AST parser to find
import spaces

import os
import tempfile
import subprocess
import pandas as pd
import gradio as gr
from fastapi import FastAPI, HTTPException, UploadFile, File
from pydantic import BaseModel
```

We will also clean up the old `try/except` block at lines 54-61.

---

## 3. Verification Plan

### Local Verification
1. Run the sandbox locally:
   ```bash
   cd sandbox
   .venv\Scripts\python app.py
   ```
2. Verify it boots without `ModuleNotFoundError` despite the top-level `import spaces`.

### Hugging Face Verification
1. Push the commit to Hugging Face.
2. Confirm the Space parses the root import, links the `@spaces.GPU` decorator, and boots successfully to **Running** state.
