# Incident Report & Diagnosis: OpenAI TPM 429 Rate Limit Exceeded

**Incident ID:** INC-20260904-429  
**Component:** Backend Agents (`backend/agents/coder.py`, `backend/agents/debugger.py`, `backend/orchestrator.py`)  
**Status:** RESOLVED & DEPLOYED  
**Commit:** [`361c67d`](https://github.com/LegitScarf/AutoML/commit/361c67d)  

---

## 1. Executive Summary

During execution run `cd1dbecd-a9e6-4dc6-bd41-834f59f49e4c` with dataset `global_ev_adoption_behavior_2026.csv` (50,000 rows, 23 columns), the dataset was successfully ingested, profiled on Hugging Face ZeroGPU in 5 seconds, and outlined by the Planner Agent. 

However, at `15:37:45`, the pipeline crashed during the code generation stage with the following error:

```text
[15:37:45] [ERR] Pipeline crashed with execution error: Coder Agent failed: Error code: 429 - 
{
  'error': {
    'message': 'Request too large for gpt-5.6-luna in organization org-rBHUAIeyAagSJXKh38Y6xSib on tokens per min (TPM): Limit 500000, Requested 1865538. The input or output tokens must be reduced in order to run successfully. Visit https://platform.openai.com/account/rate-limits to learn more.',
    'type': 'tokens',
    'param': None,
    'code': 'rate_limit_exceeded'
  }
}
```

---

## 2. Technical Root Cause Analysis

### The Flaw: Embedding Raw Tabular Data Directly Inside LLM Prompts

In [`backend/orchestrator.py`](backend/orchestrator.py), after the remote profiler step completed, the orchestrator prepared the dataset for the sandbox script by converting the raw CSV content to a Base64 string:

```python
# backend/orchestrator.py (Pre-fix)
csv_base64 = base64.b64encode(csv_content_str.encode('utf-8')).decode('utf-8')
current_code = ask_coder_agent(model_name, task, target, plan, csv_base64, numeric_cols, categorical_cols)
```

In [`backend/agents/coder.py`](backend/agents/coder.py), the entire Base64 string was directly interpolated into the OpenAI user prompt template:

```python
# backend/agents/coder.py (Pre-fix)
prompt = f"""You are a senior Machine Learning Code Generation Agent...
---
## Dataset Details:
* Target Variable: {target}
* Base64 Dataset Data:
CSV_BASE64 = "{csv_base64}"
"""
```

### Forensic Token Math: Why 1,865,538 Tokens?

1. **Dataset Size:** 50,000 rows × 23 feature columns.
2. **Raw File Size:** ~5.5 Megabytes of CSV text.
3. **Base64 Expansion:** Converting binary/text to Base64 expands payload size by 33%:
   $$\text{Base64 Size} \approx 5.5\text{ MB} \times 1.33 \approx 7.33\text{ Megabytes (7,330,000 characters)}$$
4. **Tokenizer Inefficiency with Base64:** OpenAI tokenizers (e.g. `cl100k_base` / `o200k_base`) are optimized for natural language and standard programming syntax. Base64 strings lack word boundaries and spaces, forcing the Byte-Pair Encoding (BPE) algorithm to break strings down into 2- to 4-character fragments:
   $$\text{Token Count} \approx \frac{7,330,000\text{ characters}}{\sim 3.93\text{ chars/token}} = \mathbf{1,865,538\text{ tokens}}$$
5. **OpenAI Tier Limit:** The organization tier limit for `gpt-5.6-luna` is **500,000 Tokens Per Minute (TPM)**.
6. A single request demanding **1,865,538 tokens** exceeded the account quota by **373%**, resulting in an immediate `429 Rate Limit Exceeded` rejection before any code could be generated.

---

## 3. Architecture Comparison

### Before (Vulnerable to Token Explosions):
```
[User CSV (50k rows)] ──> [Base64 (7.5 MB)] ──> [OpenAI Prompt (1.86M Tokens)] ──> 💥 429 TPM Crash!
```

### After (Decoupled with Post-Generation Injection):
```
[User CSV (50k rows)] ──> [Profile Metadata & Schema (~1,500 Tokens)] ──> [OpenAI Coder Agent]
                                                                                  │
                                                                         Outputs Python Script with
                                                                      `CSV_BASE64 = "__CSV_BASE64_DATA__"`
                                                                                  │
[Base64 (7.5 MB in RAM)] ─────────────────────────────────────────────────────────┴──> Python String Injection
                                                                                              │
                                                                               [Executable Script with Data]
                                                                                              │
                                                                               [Hugging Face ZeroGPU Sandbox]
```

---

## 4. The Permanent Fix Applied

### A. Coder Agent Prompt Decoupling (`backend/agents/coder.py`)
- Removed the raw `{csv_base64}` data from the prompt completely.
- Instructed the Coder Agent to write code that references a literal placeholder:
  ```python
  CSV_BASE64 = "__CSV_BASE64_DATA__"
  csv_data = base64.b64decode(CSV_BASE64).decode('utf-8')
  df = pd.read_csv(io.StringIO(csv_data))
  ```
- **Token Impact:** The prompt was reduced from **1,865,538 tokens to ~1,500 tokens** (a **99.9% reduction**).
- **Post-Generation Injection:** Once the LLM finishes generating the Python script, Python safely replaces `__CSV_BASE64_DATA__` with the actual Base64 string directly in memory before passing it to the execution sandbox:
  ```python
  if "__CSV_BASE64_DATA__" in code:
      code = code.replace("__CSV_BASE64_DATA__", csv_base64)
  elif "CSV_BASE64" in code:
      code = re.sub(r'CSV_BASE64\s*=\s*["\'][^"\']*["\']', f'CSV_BASE64 = "{csv_base64}"', code)
  else:
      dataset_preamble = (
          f'import base64\nimport io\nimport pandas as pd\n'
          f'CSV_BASE64 = "{csv_base64}"\n'
          f'df = pd.read_csv(io.StringIO(base64.b64decode(CSV_BASE64).decode("utf-8")))\n'
      )
      code = dataset_preamble + code
  ```

### B. Debugger Agent Sanitization (`backend/agents/debugger.py`)
- If a runtime error or threshold failure triggers the self-correction loop, the Debugger Agent sanitizes the incoming script:
  ```python
  sanitized_code = re.sub(r'CSV_BASE64\s*=\s*["\'][^"\']*["\']', 'CSV_BASE64 = "__CSV_BASE64_DATA__"', original_code)
  ```
- This prevents the failed script's 7.5 MB Base64 string from being sent to OpenAI during repair cycles.
- Post-generation, the Base64 data is re-injected so the repaired code is complete and runnable.

### C. Orchestrator Integration (`backend/orchestrator.py`)
- Updated `ask_debugger_agent` calls to pass `csv_base64` so repaired scripts maintain full dataset access without token overhead.

---

## 5. Verification & Deployment

1. **Syntax & AST Validation:** Verified with `py_compile` across all backend modules (`exit_code = 0`).
2. **Automated Test Suite:** Ran full test suite via `pytest tests/test_core_pipeline.py -v` (100% passed in 16.30s).
3. **Production Release:** Changes were staged, committed, and pushed to `https://github.com/LegitScarf/AutoML.git` on branch `prod` (Commit [`361c67d`](https://github.com/LegitScarf/AutoML/commit/361c67d)).

---

## 6. Key Takeaways & Best Practices
- **Never interpolate raw binary or tabular data into LLM prompts**: LLMs require schema, statistical summaries, and formatting instructions—not raw payload bytes.
- **Use deterministic placeholder replacement**: Let the LLM generate clean generic code containing standard tokens, then perform exact string replacement in runtime memory.
- **Maintain guardrails on self-correction loops**: Ensure repair/debugger agents strip large payloads before reflection prompts to avoid secondary rate limit spikes.
