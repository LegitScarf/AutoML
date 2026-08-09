# Fix Plan: Hugging Face Space Runtime Error

## Root Cause Analysis

The crash is a **Python package version incompatibility** between our pinned `gradio==4.31.0` and the version of `huggingface_hub` that Hugging Face Spaces pre-installs in its Python 3.10 runtime environment.

### The Chain of Events

```
HF Spaces launches app.py
  └─> import gradio             (gradio 4.31.0 from our requirements.txt)
        └─> imports oauth.py
              └─> from huggingface_hub import HfFolder   ← CRASH
```

`HfFolder` was a class inside `huggingface_hub` that was **deprecated and fully removed** in `huggingface_hub >= 0.25.0` (released January 2025). The Hugging Face Spaces environment ships with a pre-installed version of `huggingface_hub` that is **newer than 0.25.0**, so `HfFolder` no longer exists in it.

`gradio 4.31.0` (released April 2024) still imports `HfFolder` directly, which crashes as soon as the app starts.

### Why Pinning `huggingface_hub` to an older version won't work

We cannot downgrade `huggingface_hub` by adding it to `requirements.txt` because:
- HF Spaces has `huggingface_hub` **system-locked** in its base image (it's baked into the runtime itself).
- Any attempt to `pip install huggingface_hub<0.25.0` will silently fail or be overridden by the system version.

---

## The Fix: Upgrade to Gradio 5.x

`Gradio 5.0` (released October 2024) completely rewrote its OAuth and hub integration modules and **removed the dependency on `HfFolder`** entirely. It is fully compatible with `huggingface_hub >= 0.25.0`.

### Changes Required

#### 1. `sandbox/requirements.txt`
Bump the gradio version pin from `4.31.0` → `5.9.1` (a stable recent 5.x release).

```diff
- gradio==4.31.0
+ gradio==5.9.1
```

#### 2. `sandbox/app.py`
The `gr.mount_gradio_app()` function signature changed slightly in Gradio 5.x. The arguments need to be adjusted:

| Gradio 4.x | Gradio 5.x |
| :--- | :--- |
| `gr.mount_gradio_app(fastapi_app, gradio_demo, path="/")` | `gr.mount_gradio_app(fastapi_app, gradio_demo, path="/ui")` |

In Gradio 5.x, mounting the Gradio UI at the root path `"/"` conflicts with FastAPI's own root. We mount the Gradio UI at `"/ui"` instead, and all our REST API endpoints (`/health`, `/profile`, `/execute`) remain accessible at the root level of the Space URL as expected by the backend.

#### 3. `sandbox/README.md`
Update the `sdk_version` field to match the new Gradio version:

```diff
- sdk_version: "4.31.0"
+ sdk_version: "5.9.1"
```

---

## Summary of Changes

| File | Type | Change |
| :--- | :--- | :--- |
| `requirements.txt` | MODIFY | `gradio==4.31.0` → `gradio==5.9.1` |
| `app.py` | MODIFY | Mount path `"/"` → `"/ui"` in `gr.mount_gradio_app()` |
| `README.md` | MODIFY | `sdk_version: "4.31.0"` → `sdk_version: "5.9.1"` |

> [!NOTE]
> These are the **only 3 minimal changes** needed. All existing endpoint logic in `app.py` (`/health`, `/profile`, `/execute`) remains completely unchanged.

---

## Verification After Fix

Once the changes are pushed, Hugging Face will rebuild the Space (takes ~2–3 minutes). The Space should show:
- ✅ Green **Running** status badge on the Space page
- ✅ The Gradio status UI visible at `https://huggingface.co/spaces/LegitScarf/automl-sandbox/ui`
- ✅ API endpoints accessible at `https://huggingface.co/spaces/LegitScarf/automl-sandbox/health`
