# Architectural Study: Transitioning to LLM-Powered Planner & Coder Agents

This study outlines the architecture to shift the Omega platform from deterministic templated logic to true LLM-powered autonomous agents using the Google Gemini API (or OpenAI API).

---

## 1. Architectural Blueprint

We will replace the static text template generation in `backend/orchestrator.py` with two dedicated agent modules that perform LLM inference:

```
                  [ Ingestion & Profiling ]
                             │
                             ▼
                    [ Planner Agent Module ]
                  - Ingests Profile & Config
                  - Prompt: Custom statistical plan instructions
                  - Call: gemini-2.0-flash / gpt-4o-mini
                             │
                             ▼ (Markdown Plan)
                    [ Coder Agent Module ]
                  - Ingests Markdown Plan + Base64 Dataset
                  - Prompt: Code compilation instructions
                  - Call: gemini-1.5-pro / gpt-4o (Higher reasoning)
                             │
                             ▼ (Raw python script)
                    [ HF Sandbox Runner ]
```

---

## 2. LLM Engine Recommendation

To keep the pipeline fast, high-quality, and cost-effective, we recommend a **hybrid-model approach**:

* **For Planning:** **Gemini 2.0 Flash** (or **GPT-4o-mini**). High speed, low latency, and highly structured markdown outlining capabilities.
* **For Coding:** **Gemini 1.5 Pro** (or **GPT-4o**). Excellent reasoning for code generation, complex imports mapping, syntax checking, and edge-case handling.

---

## 3. Modular File Structure

We will separate the agent code into a clean `agents/` submodule package:

1. **`backend/agents/planner.py` [NEW]:**
   Defines `ask_planner_agent`. Formulates the prompt with the dataset schema, configures temperature (e.g. 0.2 for analytical structure), and returns the plan.
2. **`backend/agents/coder.py` [NEW]:**
   Defines `ask_coder_agent`. Embeds the base64 data, passes the plan checklist, sets temperature to 0.0 (maximum determinism and syntax accuracy), and filters/strips any markdown block code tags (` ```python `) from the LLM response.
3. **`backend/agents/config.py` [NEW]:**
   Manages client initialization (Google `google-generativeai` or `openai` client instantiation based on active environment variables).

---

## 4. Key Improvements Over Determinism

* **Real Statistical Adaptability:** Instead of a generic VIF checklist, the Planner can inspect the distribution of null values, column cardinality, and skewness to plan custom imputations or logarithmic transformations if features are highly skewed.
* **Algorithmic Extensibility:** The frontend lists models like XGBoost, LightGBM, SVM, and CatBoost. If the LLM coder receives the plan, it writes the exact syntax for each package natively, eliminating the need to maintain hundreds of hardcoded template variations.
* **Self-Healing Loop Ready:** Having an LLM Coder makes it possible to implement a self-correcting compiler loop (e.g., if execution fails in the sandbox, feed the traceback error back to the Coder Agent to fix the script and re-run!).
