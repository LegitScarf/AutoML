import streamlit as st
import requests
import os

st.set_page_config(
    page_title="Agentic AutoML Dashboard",
    page_icon="🛰️",
    layout="wide"
)

# ----------------------------------------------------------------------------
# DESIGN TOKENS
# Paper (#FFFFFF) background · Ink text · Signal Blue primary accent ·
# Circuit Teal secondary accent · status colors reused for the pipeline stepper
# Type: Space Grotesk (display) + Inter (body) + JetBrains Mono (data/labels)
# ----------------------------------------------------------------------------
st.markdown("""
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@500;600;700&family=Inter:wght@400;500;600&family=JetBrains+Mono:wght@400;500&display=swap" rel="stylesheet">

<style>
:root {
    --paper: #FFFFFF;
    --mist: #F6F8FB;
    --mist-2: #EEF2F8;
    --ink: #0F172A;
    --slate: #64748B;
    --border: #E2E8F0;
    --signal: #2554F6;
    --signal-dark: #1B3FCC;
    --signal-soft: #EAEFFE;
    --teal: #0EA5A5;
    --success: #16A34A;
    --success-soft: #EAFBF1;
    --warning: #D97706;
    --warning-soft: #FEF6E7;
    --error: #DC2626;
    --error-soft: #FDEDED;
}

html, body, [class*="css"] {
    font-family: 'Inter', sans-serif;
}

.stApp {
    background: var(--paper);
}

[data-testid="stHeader"] {
    background: rgba(255,255,255,0.0);
}

.block-container {
    padding-top: 2.2rem;
    max-width: 980px;
}

/* ---------- Header ---------- */
.hero-eyebrow {
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.72rem;
    letter-spacing: 0.14em;
    text-transform: uppercase;
    color: var(--teal);
    font-weight: 500;
    margin-bottom: 0.5rem;
}
.hero-title {
    font-family: 'Space Grotesk', sans-serif;
    font-weight: 700;
    font-size: 2.35rem;
    color: var(--ink);
    line-height: 1.15;
    margin-bottom: 0.55rem;
    letter-spacing: -0.01em;
}
.hero-sub {
    font-size: 1rem;
    color: var(--slate);
    max-width: 640px;
    line-height: 1.55;
    margin-bottom: 2rem;
}

/* ---------- Pipeline stepper (signature element) ---------- */
.stepper-wrap {
    display: flex;
    align-items: center;
    justify-content: space-between;
    background: var(--mist);
    border: 1px solid var(--border);
    border-radius: 14px;
    padding: 1.1rem 1.4rem;
    margin-bottom: 2.2rem;
}
.step {
    display: flex;
    align-items: center;
    gap: 0.6rem;
    flex: 1;
}
.step-dot {
    width: 30px;
    height: 30px;
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.75rem;
    font-weight: 500;
    flex-shrink: 0;
    border: 2px solid var(--border);
    background: var(--paper);
    color: var(--slate);
    transition: all 0.25s ease;
}
.step-label {
    font-size: 0.82rem;
    font-weight: 500;
    color: var(--slate);
    white-space: nowrap;
}
.step-line {
    height: 2px;
    flex: 1;
    background: var(--border);
    margin: 0 0.3rem;
    transition: background 0.25s ease;
}
.step.idle .step-dot { border-color: var(--border); color: var(--slate); }
.step.active .step-dot { border-color: var(--signal); background: var(--signal); color: white; box-shadow: 0 0 0 4px var(--signal-soft); }
.step.active .step-label { color: var(--ink); font-weight: 600; }
.step.done .step-dot { border-color: var(--success); background: var(--success); color: white; }
.step.done .step-label { color: var(--ink); }
.step.error .step-dot { border-color: var(--error); background: var(--error); color: white; }
.step.error .step-label { color: var(--error); font-weight: 600; }
.line-filled { background: var(--success) !important; }

/* ---------- Section labels ---------- */
.section-label {
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.72rem;
    letter-spacing: 0.1em;
    text-transform: uppercase;
    color: var(--slate);
    font-weight: 500;
    margin: 1.6rem 0 0.6rem 0;
}

/* ---------- Config card ---------- */
[data-testid="stVerticalBlockBorderWrapper"] {
    border-radius: 16px !important;
}
div[data-testid="column"] {
    padding: 0 0.4rem;
}

/* ---------- Inputs ---------- */
[data-testid="stTextInput"] label {
    font-size: 0.85rem;
    font-weight: 600;
    color: var(--ink);
}
[data-testid="stTextInput"] input {
    background: var(--mist);
    border: 1.5px solid var(--border);
    border-radius: 10px;
    color: var(--ink);
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.88rem;
    padding: 0.6rem 0.8rem;
    transition: border-color 0.2s ease, background 0.2s ease;
}
[data-testid="stTextInput"] input:focus {
    border-color: var(--signal);
    background: var(--paper);
    box-shadow: 0 0 0 3px var(--signal-soft);
}
[data-testid="stTextInput"] [data-testid="stTooltipHoverTarget"] svg {
    color: var(--slate);
}

/* ---------- Primary button ---------- */
[data-testid="stButton"] button {
    background: var(--signal);
    color: white;
    border: none;
    border-radius: 10px;
    padding: 0.7rem 1.6rem;
    font-weight: 600;
    font-size: 0.95rem;
    letter-spacing: 0.01em;
    box-shadow: 0 1px 2px rgba(37,84,246,0.15);
    transition: all 0.18s ease;
    margin-top: 0.4rem;
}
[data-testid="stButton"] button:hover {
    background: var(--signal-dark);
    box-shadow: 0 4px 14px rgba(37,84,246,0.28);
    transform: translateY(-1px);
}
[data-testid="stButton"] button:active {
    transform: translateY(0px);
}

/* ---------- Link button (download) ---------- */
[data-testid="stLinkButton"] a {
    background: var(--success) !important;
    color: white !important;
    border: none !important;
    border-radius: 10px !important;
    font-weight: 600 !important;
    box-shadow: 0 1px 2px rgba(22,163,74,0.18);
}
[data-testid="stLinkButton"] a:hover {
    background: #128a3e !important;
    box-shadow: 0 4px 14px rgba(22,163,74,0.28);
}

/* ---------- Alerts ---------- */
[data-testid="stAlert"] {
    border-radius: 12px;
    border: 1px solid var(--border);
    font-size: 0.9rem;
}

/* ---------- JSON viewer ---------- */
[data-testid="stJson"] {
    background: var(--mist) !important;
    border: 1px solid var(--border);
    border-radius: 12px;
    padding: 0.4rem;
}

/* ---------- Subheaders ---------- */
h3 {
    font-family: 'Space Grotesk', sans-serif !important;
    color: var(--ink) !important;
    font-weight: 600 !important;
}

/* ---------- Divider ---------- */
hr {
    border-color: var(--border) !important;
}
</style>
""", unsafe_allow_html=True)


def render_stepper(status: str):
    """
    Renders the four-stage agentic pipeline as a horizontal stepper.
    status: 'idle' | 'running' | 'success' | 'error'
    This is purely presentational and reflects st.session_state, it does
    not alter any request/response logic below.
    """
    stages = ["Profile", "Generate", "Execute", "Self-Correct"]

    if status == "idle":
        stage_states = ["idle"] * 4
        line_filled = [False, False, False]
    elif status == "running":
        stage_states = ["active", "active", "active", "active"]
        line_filled = [True, True, True]
    elif status == "success":
        stage_states = ["done", "done", "done", "done"]
        line_filled = [True, True, True]
    else:  # error
        stage_states = ["done", "active", "error", "idle"]
        line_filled = [True, True, False]

    html = '<div class="stepper-wrap">'
    for i, (label, state) in enumerate(zip(stages, stage_states)):
        html += f'''
        <div class="step {state}">
            <div class="step-dot">{i+1}</div>
            <div class="step-label">{label}</div>
        </div>'''
        if i < 3:
            line_cls = "step-line line-filled" if line_filled[i] else "step-line"
            html += f'<div class="{line_cls}"></div>'
    html += '</div>'
    st.markdown(html, unsafe_allow_html=True)


if "pipeline_status" not in st.session_state:
    st.session_state.pipeline_status = "idle"

# ---------------------------------------------------------------------------
# HEADER
# ---------------------------------------------------------------------------
st.markdown('<div class="hero-eyebrow">Agentic ML Ops</div>', unsafe_allow_html=True)
st.markdown('<div class="hero-title">Agentic AutoML Orchestrator</div>', unsafe_allow_html=True)
st.markdown(
    '<div class="hero-sub">Upload a dataset, specify the target column, and let the AI system '
    'profile, generate, execute, and self-correct your ML training pipeline.</div>',
    unsafe_allow_html=True
)

render_stepper(st.session_state.pipeline_status)

# ---------------------------------------------------------------------------
# CONFIGURATION
# ---------------------------------------------------------------------------
st.markdown('<div class="section-label">Pipeline Configuration</div>', unsafe_allow_html=True)

config_card = st.container(border=True)
with config_card:
    webhook_url = st.text_input(
        "n8n Webhook URL",
        value="http://localhost:5678/webhook-test/trigger-automl",
        help="Enter your local or public ngrok n8n webhook URL."
    )

    col1, col2 = st.columns(2)

    with col1:
        dataset_path = st.text_input(
            "Dataset Path (Local to host)",
            value="c:/Users/KIIT/Desktop/AutoML/sample_dataset.csv",
            help="The local file path that the Sandbox container/MCP servers can read."
        )

    with col2:
        target_variable = st.text_input(
            "Target Variable",
            value="purchased",
            help="The column name you want the model to predict."
        )

    trigger = st.button("🚀 Trigger AutoML Pipeline", type="primary")

# ---------------------------------------------------------------------------
# EXECUTION — logic unchanged from the original implementation
# ---------------------------------------------------------------------------
if trigger:
    if not webhook_url:
        st.error("Please enter a valid webhook URL.")
    elif not dataset_path:
        st.error("Please enter a dataset path.")
    elif not target_variable:
        st.error("Please enter a target variable.")
    else:
        st.session_state.pipeline_status = "running"
        st.info("Triggering n8n workflow...")

        payload = {
            "file_path": dataset_path,
            "target_variable": target_variable
        }

        try:
            with st.spinner("Pipeline is running... Check n8n dashboard for real-time progress."):
                response = requests.post(webhook_url, json=payload, timeout=300)

            if response.status_code == 200:
                st.session_state.pipeline_status = "success"
                st.success("AutoML pipeline finished successfully!")
                res_data = response.json()

                st.markdown('<div class="section-label">Pipeline Response</div>', unsafe_allow_html=True)
                st.json(res_data)

                # Retrieve download URL
                download_url = None
                if isinstance(res_data, dict):
                    download_url = res_data.get("download_url")
                elif isinstance(res_data, list) and len(res_data) > 0:
                    download_url = res_data[0].get("download_url")

                if download_url:
                    # Map host.docker.internal to localhost for host browser access
                    local_url = download_url.replace("host.docker.internal", "localhost")
                    st.markdown('<div class="section-label">Your Model is Ready</div>', unsafe_allow_html=True)
                    st.link_button("📥 Download AutoML Bundle (.zip)", local_url, type="primary")
            else:
                st.session_state.pipeline_status = "error"
                st.error(f"Error triggering pipeline. Status code: {response.status_code}")
                st.text(response.text)

        except Exception as e:
            st.session_state.pipeline_status = "error"
            st.error(f"Failed to connect to webhook: {str(e)}")
            st.info("Make sure n8n is running and 'Listen for test event' or 'Execute workflow' is active.")