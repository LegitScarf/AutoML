# Architectural Study: Multi-Agent Self-Correction Loop in Omega

This study details the architectural design to integrate true LLM-driven Planner, Coder, and Debug (Self-Correction) Agents into the live Omega platform, powered by OpenAI's `gpt-5.6-luna` model.

---

## 1. Architectural Model & Interactions

The architecture replaces deterministic steps with a state-aware agentic circle. The backend orchestrator acts as the "kernel" that schedules task handoffs, handles sandbox isolation, and evaluates success criteria.

```
       [ Upload Dataset ]
               │
               ▼
      [ Profiler Agent ]
               │
               ▼
      [ Planner Agent ]  ──► Generates detailed Markdown data prep & training plan
               │
               ▼
       [ Coder Agent ]   ──► Generates initial Python script embedding base64 CSV
               │
               ▼
     ┌─► [ HF Sandbox ]  ──► Executes script & captures exit_code, stdout, stderr, zip_base64
     │         │
     │         ▼
     │   [ Success? ] ──► (Yes) ──► [ Complete ] (ZIP decoded & served)
     │         │
     │       (No) ➔ (exit_code != 0 OR score < min_threshold)
     │         │
     └─ [ Debug Agent ]  ──► Reads stderr/score. Rewrites script using GPT-5.6-Luna (Loops max 3x)
```

---

## 2. Agent Node Definitions (Powered by `gpt-5.6-luna`)

We will configure the OpenAI client in the backend to query `model="gpt-5.6-luna"`.

### A. Planner Agent
* **Role:** Statistical Architect.
* **Input:** Column names, data types, null count distributions, target column, task type, and model selected.
* **Prompt:** Instructs the LLM to write a comprehensive data cleaning, multicollinearity testing (VIF checks), validation splitting, model training, and diagnostic charting plan in markdown format.

### B. Coder Agent
* **Role:** Machine Learning Coder.
* **Input:** Dataset profile, Markdown Plan, and raw base64-encoded CSV dataset.
* **Prompt:** Translates the plan into a working Python script. The script must execute entirely in memory by decoding the base64 CSV string. It must save `model.pkl`, `preprocessor.pkl`, requirements, a README, and diagnostic PNG plots.

### C. Debug Agent (Self-Correction Loop)
* **Role:** Code Debugger and Optimizer.
* **Input:** Failed Python script code, exit code, execution standard logs, standard error trace, user validation metric threshold, and current metric score.
* **Prompt:** 
  * If the script crashed (exit code $\neq 0$), analyzes the trace, resolves the syntax/logic bug, and outputs corrected Python code.
  * If validation performance fails to meet the `min_threshold`, broadens hyperparameter search grids, modifies scaling approaches, or introduces polynomial features to boost score.

---

## 3. Orchestration & State Machine Modifications

* **Max Iterations Check:** The loop in `backend/orchestrator.py` will have a safety check counter (`MAX_ATTEMPTS = 3`).
* **Stdout Metric Parser:** The orchestrator reads `[METRIC] {metric_name} = {score}` from sandbox stdout. If `score < run.min_threshold`, it marks the run as a performance failure and passes the code to the Debug Agent to optimize it.
* **Sanitization Layer:** All agent responses are run through a regex parser to strip markdown fences (` ```python `) and extract raw code blocks.
