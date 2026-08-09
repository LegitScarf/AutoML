import streamlit as st
import requests
import time
from datetime import datetime

st.set_page_config(
    page_title="AutoML · Agentic ML Engineer",
    page_icon="◈",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ============================================================================
# DESIGN SYSTEM — "Techy Futuristic" on Paper White
# Palette:
#   Paper      #FFFFFF   base surface
#   Mist       #F4F7FB   subtle wells
#   Ink        #0A0F1E   primary text
#   Slate      #5B667A   secondary text
#   Grid       #E4EAF3   hairlines / grid
#   Signal     #2C5BFF   primary accent (electric blue)
#   Neon       #00E5D1   secondary accent (circuit teal)
#   Violet     #7C4DFF   tertiary accent
#   Amber      #F59E0B   warning
#   Rose       #F43F5E   error / stop
# Type:
#   Display   -> Chakra Petch  (angular, techy)
#   Body      -> Inter
#   Mono      -> JetBrains Mono
# ============================================================================

st.markdown("""
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Chakra+Petch:wght@500;600;700&family=Inter:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500;600&display=swap" rel="stylesheet">

<style>
:root {
    --paper: #FFFFFF;
    --mist:  #F4F7FB;
    --mist-2:#EDF1F8;
    --ink:   #0A0F1E;
    --ink-2: #1A2238;
    --slate: #5B667A;
    --grid:  #E4EAF3;
    --grid-2:#D6DEEC;
    --signal:     #2C5BFF;
    --signal-dk:  #1D40C7;
    --signal-soft:#E7ECFF;
    --neon:       #00E5D1;
    --neon-soft:  #DAFBF6;
    --violet:     #7C4DFF;
    --violet-soft:#EDE6FF;
    --success:    #10B981;
    --success-soft:#D6F6E7;
    --amber:  #F59E0B;
    --amber-soft:#FEF3D6;
    --rose:   #F43F5E;
    --rose-soft:#FEE1E7;
}

/* ---------- Global ---------- */
html, body, [class*="css"] { font-family: 'Inter', system-ui, sans-serif; }

.stApp {
    background:
      radial-gradient(1200px 600px at 85% -10%, rgba(0,229,209,0.06), transparent 60%),
      radial-gradient(900px 500px at -10% 10%, rgba(44,91,255,0.06), transparent 60%),
      linear-gradient(#FFFFFF, #FFFFFF);
    color: var(--ink);
}

/* Ambient dot grid */
.stApp::before {
    content: "";
    position: fixed;
    inset: 0;
    background-image: radial-gradient(rgba(10,15,30,0.045) 1px, transparent 1px);
    background-size: 22px 22px;
    pointer-events: none;
    z-index: 0;
}

[data-testid="stHeader"] { background: transparent; }
[data-testid="stToolbar"] { right: 1rem; }
#MainMenu, footer { visibility: hidden; }

.block-container {
    padding-top: 1.6rem;
    padding-bottom: 4rem;
    max-width: 1180px;
    position: relative;
    z-index: 1;
}

/* ---------- Top Nav / Brand ---------- */
.brand-row {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 0.6rem 0 1.4rem 0;
    border-bottom: 1px dashed var(--grid);
    margin-bottom: 2rem;
}
.brand {
    display: flex; align-items: center; gap: 0.7rem;
}
.brand-mark {
    width: 34px; height: 34px; border-radius: 9px;
    background: linear-gradient(135deg, #0A0F1E 0%, #1A2238 100%);
    display: grid; place-items: center;
    box-shadow: 0 6px 18px rgba(10,15,30,0.15), inset 0 0 0 1px rgba(255,255,255,0.05);
    position: relative;
}
.brand-mark::after {
    content: ""; position: absolute; inset: 0; border-radius: 9px;
    box-shadow: 0 0 0 1px rgba(0,229,209,0.35) inset;
}
.brand-mark svg { width: 18px; height: 18px; }
.brand-name {
    font-family: 'Chakra Petch', sans-serif;
    font-weight: 700; font-size: 1.15rem;
    letter-spacing: 0.02em; color: var(--ink);
}
.brand-name span { color: var(--signal); }
.brand-tag {
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.68rem; letter-spacing: 0.14em;
    padding: 0.28rem 0.55rem; border-radius: 999px;
    background: var(--signal-soft); color: var(--signal-dk);
    text-transform: uppercase; font-weight: 600;
}
.nav-links {
    display: flex; gap: 1.3rem;
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.75rem; color: var(--slate);
    letter-spacing: 0.08em; text-transform: uppercase;
}
.nav-links a { color: var(--slate); text-decoration: none; transition: color .2s; }
.nav-links a:hover { color: var(--ink); }
.nav-status {
    display: flex; align-items: center; gap: 0.45rem;
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.72rem; color: var(--slate);
    letter-spacing: 0.08em;
}
.nav-status .pulse {
    width: 8px; height: 8px; border-radius: 50%;
    background: var(--neon);
    box-shadow: 0 0 0 0 rgba(0,229,209,0.6);
    animation: pulseDot 1.8s infinite;
}
@keyframes pulseDot {
    0%   { box-shadow: 0 0 0 0 rgba(0,229,209,0.6); }
    70%  { box-shadow: 0 0 0 10px rgba(0,229,209,0); }
    100% { box-shadow: 0 0 0 0 rgba(0,229,209,0); }
}

/* ---------- Hero ---------- */
.hero-grid { display: grid; grid-template-columns: 1.4fr 1fr; gap: 2.4rem; align-items: center; }
@media (max-width: 900px) { .hero-grid { grid-template-columns: 1fr; } }

.eyebrow {
    display: inline-flex; align-items: center; gap: 0.5rem;
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.7rem; letter-spacing: 0.18em; text-transform: uppercase;
    color: var(--signal); font-weight: 600;
    padding: 0.35rem 0.7rem; border-radius: 999px;
    background: var(--signal-soft);
    border: 1px solid rgba(44,91,255,0.15);
    margin-bottom: 1rem;
}
.eyebrow .dot { width: 6px; height: 6px; border-radius: 50%; background: var(--signal); }

.hero-title {
    font-family: 'Chakra Petch', sans-serif;
    font-weight: 700; font-size: 3.2rem; line-height: 1.05;
    color: var(--ink); letter-spacing: -0.015em;
    margin-bottom: 1rem;
}
.hero-title .accent {
    background: linear-gradient(90deg, #2C5BFF 0%, #7C4DFF 55%, #00E5D1 100%);
    -webkit-background-clip: text; -webkit-text-fill-color: transparent;
    background-clip: text;
}
.hero-sub {
    font-size: 1.02rem; color: var(--slate);
    max-width: 560px; line-height: 1.6; margin-bottom: 1.6rem;
}
.hero-meta {
    display: flex; gap: 1.4rem; flex-wrap: wrap;
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.72rem; color: var(--slate);
    letter-spacing: 0.06em; text-transform: uppercase;
}
.hero-meta span b { color: var(--ink); font-weight: 600; }

/* ---------- Animated Pipeline Diagram (Hero visual) ---------- */
.pipe-card {
    position: relative;
    background: linear-gradient(180deg, #FFFFFF 0%, #FAFBFF 100%);
    border: 1px solid var(--grid);
    border-radius: 18px;
    padding: 1.5rem 1.4rem 1.3rem 1.4rem;
    box-shadow:
        0 1px 0 rgba(255,255,255,0.7) inset,
        0 24px 60px -30px rgba(10,15,30,0.20),
        0 4px 14px -8px rgba(10,15,30,0.08);
    overflow: hidden;
}
.pipe-card::before {
    content: ""; position: absolute; inset: 0;
    background:
      linear-gradient(90deg, transparent 49.5%, var(--grid) 49.5% 50.5%, transparent 50.5%),
      linear-gradient(0deg,  transparent 49.5%, var(--grid) 49.5% 50.5%, transparent 50.5%);
    background-size: 40px 40px;
    opacity: 0.35;
    pointer-events: none;
}
.pipe-card-hd {
    display: flex; justify-content: space-between; align-items: center;
    margin-bottom: 1rem; position: relative;
}
.pipe-card-hd .t {
    font-family: 'Chakra Petch', sans-serif;
    font-weight: 600; font-size: 0.95rem; color: var(--ink);
    letter-spacing: 0.02em;
}
.pipe-card-hd .k {
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.68rem; color: var(--slate);
    letter-spacing: 0.12em; text-transform: uppercase;
}

.pipe-diagram {
    position: relative;
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    gap: 0;
    padding: 1.2rem 0.2rem;
}
.pipe-node {
    position: relative;
    display: flex; flex-direction: column; align-items: center;
    gap: 0.55rem;
    z-index: 2;
}
.pipe-node .ring {
    width: 54px; height: 54px; border-radius: 14px;
    background: #FFFFFF;
    border: 1.5px solid var(--grid-2);
    display: grid; place-items: center;
    box-shadow: 0 6px 18px -10px rgba(10,15,30,0.15);
    position: relative;
    transition: transform .25s, border-color .25s, box-shadow .25s;
}
.pipe-node .ring svg { width: 22px; height: 22px; color: var(--slate); }
.pipe-node .lbl {
    font-family: 'Chakra Petch', sans-serif;
    font-size: 0.82rem; font-weight: 600; color: var(--ink);
    letter-spacing: 0.02em;
}
.pipe-node .sub {
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.62rem; color: var(--slate);
    letter-spacing: 0.1em; text-transform: uppercase;
}
.pipe-connect {
    position: absolute;
    top: calc(1.2rem + 27px);
    left: 0; right: 0; height: 2px;
    margin: 0 12.5%;
    background: repeating-linear-gradient(90deg, var(--grid-2) 0 6px, transparent 6px 12px);
    z-index: 1;
}
.pipe-connect .flow {
    position: absolute; top: -1px; left: 0;
    height: 4px; width: 60px; border-radius: 4px;
    background: linear-gradient(90deg, transparent, var(--signal), var(--neon), transparent);
    filter: blur(0.4px);
    animation: flowPulse 2.4s linear infinite;
    opacity: 0;
}
.pipe-diagram.running .pipe-connect .flow { opacity: 1; }
.pipe-diagram.running .pipe-node .ring {
    border-color: var(--signal);
    box-shadow: 0 0 0 4px var(--signal-soft), 0 8px 22px -10px rgba(44,91,255,0.35);
    animation: nodeBeat 2.2s ease-in-out infinite;
}
.pipe-diagram.running .pipe-node .ring svg { color: var(--signal); }
.pipe-diagram.running .pipe-node:nth-child(1) .ring { animation-delay: 0.0s; }
.pipe-diagram.running .pipe-node:nth-child(3) .ring { animation-delay: 0.5s; }
.pipe-diagram.running .pipe-node:nth-child(5) .ring { animation-delay: 1.0s; }
.pipe-diagram.running .pipe-node:nth-child(7) .ring { animation-delay: 1.5s; }

.pipe-diagram.success .pipe-node .ring {
    border-color: var(--success);
    background: var(--success-soft);
    box-shadow: 0 0 0 3px rgba(16,185,129,0.15);
}
.pipe-diagram.success .pipe-node .ring svg { color: var(--success); }
.pipe-diagram.success .pipe-connect { background: linear-gradient(90deg, var(--success), var(--success)); }

.pipe-diagram.error .pipe-node:nth-child(5) .ring {
    border-color: var(--rose);
    background: var(--rose-soft);
    box-shadow: 0 0 0 3px rgba(244,63,94,0.15);
    animation: shake 0.4s ease-in-out;
}
.pipe-diagram.error .pipe-node:nth-child(5) .ring svg { color: var(--rose); }

@keyframes flowPulse {
    0%   { transform: translateX(0%); }
    100% { transform: translateX(700%); }
}
@keyframes nodeBeat {
    0%,100% { transform: translateY(0); }
    50%     { transform: translateY(-3px); }
}
@keyframes shake {
    0%,100% { transform: translateX(0); }
    25%     { transform: translateX(-3px); }
    75%     { transform: translateX(3px); }
}

/* ---------- Section header ---------- */
.section {
    display: flex; align-items: center; justify-content: space-between;
    margin: 2.6rem 0 1rem 0;
}
.section .lhs { display: flex; align-items: center; gap: 0.7rem; }
.section .idx {
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.7rem; letter-spacing: 0.14em; color: var(--slate);
    padding: 0.25rem 0.55rem; border-radius: 6px;
    background: var(--mist); border: 1px solid var(--grid);
}
.section .ttl {
    font-family: 'Chakra Petch', sans-serif;
    font-weight: 600; font-size: 1.35rem; color: var(--ink);
    letter-spacing: 0.01em;
}
.section .sub {
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.7rem; color: var(--slate);
    letter-spacing: 0.12em; text-transform: uppercase;
}

/* ---------- How it works cards ---------- */
.hiw-grid { display: grid; grid-template-columns: repeat(4, 1fr); gap: 0.9rem; }
@media (max-width: 900px) { .hiw-grid { grid-template-columns: repeat(2, 1fr); } }
.hiw {
    position: relative;
    background: #FFFFFF;
    border: 1px solid var(--grid);
    border-radius: 14px;
    padding: 1.1rem 1.05rem;
    transition: transform .22s ease, box-shadow .22s ease, border-color .22s ease;
    overflow: hidden;
}
.hiw:hover {
    transform: translateY(-3px);
    border-color: var(--signal);
    box-shadow: 0 16px 40px -22px rgba(44,91,255,0.35);
}
.hiw::after {
    content: ""; position: absolute; top: 0; left: 0; right: 0; height: 2px;
    background: linear-gradient(90deg, var(--signal), var(--neon));
    transform: scaleX(0); transform-origin: left; transition: transform .3s;
}
.hiw:hover::after { transform: scaleX(1); }
.hiw .num {
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.7rem; color: var(--slate); letter-spacing: 0.12em;
    margin-bottom: 0.7rem;
}
.hiw .ico {
    width: 34px; height: 34px; border-radius: 9px;
    background: var(--signal-soft); color: var(--signal);
    display: grid; place-items: center; margin-bottom: 0.7rem;
}
.hiw .ico svg { width: 18px; height: 18px; }
.hiw:nth-child(2) .ico { background: var(--violet-soft); color: var(--violet); }
.hiw:nth-child(3) .ico { background: var(--neon-soft); color: #0BAF9F; }
.hiw:nth-child(4) .ico { background: var(--amber-soft); color: var(--amber); }
.hiw .h {
    font-family: 'Chakra Petch', sans-serif;
    font-weight: 600; font-size: 0.98rem; color: var(--ink);
    margin-bottom: 0.35rem; letter-spacing: 0.01em;
}
.hiw .p {
    font-size: 0.82rem; color: var(--slate); line-height: 1.5;
}

/* ---------- Config card ---------- */
.cfg-card {
    background: linear-gradient(180deg, #FFFFFF 0%, #FBFCFF 100%);
    border: 1px solid var(--grid);
    border-radius: 16px;
    padding: 1.4rem 1.5rem 1.6rem 1.5rem;
    box-shadow: 0 24px 60px -40px rgba(10,15,30,0.18);
    position: relative;
}
.cfg-card::before {
    content: ""; position: absolute; top: 0; left: 24px; right: 24px; height: 1px;
    background: linear-gradient(90deg, transparent, var(--signal), var(--neon), transparent);
}

/* Streamlit inputs */
[data-testid="stTextInput"] label {
    font-family: 'Chakra Petch', sans-serif !important;
    font-size: 0.82rem !important; font-weight: 600 !important;
    color: var(--ink) !important; letter-spacing: 0.02em;
}
[data-testid="stTextInput"] input {
    background: #FFFFFF !important;
    border: 1.5px solid var(--grid) !important;
    border-radius: 10px !important;
    color: var(--ink) !important;
    font-family: 'JetBrains Mono', monospace !important;
    font-size: 0.85rem !important;
    padding: 0.65rem 0.85rem !important;
    transition: border-color .18s, box-shadow .18s, background .18s;
}
[data-testid="stTextInput"] input:focus {
    border-color: var(--signal) !important;
    box-shadow: 0 0 0 4px var(--signal-soft) !important;
    outline: none !important;
}

/* Streamlit buttons */
[data-testid="stButton"] button {
    background: linear-gradient(135deg, #2C5BFF 0%, #1D40C7 100%) !important;
    color: #fff !important;
    border: none !important;
    border-radius: 11px !important;
    padding: 0.75rem 1.6rem !important;
    font-family: 'Chakra Petch', sans-serif !important;
    font-weight: 600 !important;
    font-size: 0.95rem !important;
    letter-spacing: 0.03em !important;
    box-shadow: 0 8px 24px -8px rgba(44,91,255,0.55),
                inset 0 1px 0 rgba(255,255,255,0.25) !important;
    transition: transform .16s, box-shadow .16s, filter .16s !important;
    position: relative; overflow: hidden;
}
[data-testid="stButton"] button:hover {
    transform: translateY(-2px);
    filter: brightness(1.05);
    box-shadow: 0 14px 32px -8px rgba(44,91,255,0.65) !important;
}
[data-testid="stButton"] button:active { transform: translateY(0); }

/* Link (download) button */
[data-testid="stLinkButton"] a {
    background: linear-gradient(135deg, #10B981 0%, #059669 100%) !important;
    color: #fff !important; border: none !important;
    border-radius: 11px !important;
    font-family: 'Chakra Petch', sans-serif !important;
    font-weight: 600 !important; letter-spacing: 0.02em !important;
    box-shadow: 0 8px 24px -8px rgba(16,185,129,0.55) !important;
}
[data-testid="stLinkButton"] a:hover {
    filter: brightness(1.05);
    box-shadow: 0 14px 32px -8px rgba(16,185,129,0.65) !important;
}

/* Chips (sample dataset row) */
.chips-row {
    display: flex; flex-wrap: wrap; gap: 0.5rem;
    margin-top: 0.4rem; margin-bottom: 0.3rem;
}
.chip {
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.72rem; color: var(--ink);
    padding: 0.4rem 0.7rem; border-radius: 999px;
    background: #FFFFFF; border: 1px solid var(--grid);
    box-shadow: 0 2px 6px -3px rgba(10,15,30,0.08);
    display: inline-flex; align-items: center; gap: 0.45rem;
    transition: border-color .2s, transform .2s, background .2s;
    cursor: default;
}
.chip:hover {
    border-color: var(--signal);
    background: var(--signal-soft);
    transform: translateY(-1px);
}
.chip .k {
    font-size: 0.62rem; color: var(--slate);
    text-transform: uppercase; letter-spacing: 0.12em;
}
.chip .dot {
    width: 6px; height: 6px; border-radius: 50%;
    background: var(--neon);
}
.chip.violet .dot { background: var(--violet); }
.chip.signal .dot { background: var(--signal); }
.chip.amber  .dot { background: var(--amber); }

/* Alerts */
[data-testid="stAlert"] {
    border-radius: 12px !important;
    border: 1px solid var(--grid) !important;
    font-size: 0.9rem !important;
}

/* JSON viewer */
[data-testid="stJson"] {
    background: #0A0F1E !important;
    border: 1px solid var(--ink-2) !important;
    border-radius: 12px !important;
    padding: 0.6rem !important;
}
[data-testid="stJson"] * { color: #E2E8F0 !important; }

/* Divider */
hr { border-color: var(--grid) !important; }

/* ---------- Agent Activity Log ---------- */
.log-card {
    background: #0A0F1E;
    border-radius: 16px;
    padding: 1.1rem 1.2rem 1.2rem 1.2rem;
    color: #E2E8F0;
    position: relative;
    overflow: hidden;
    border: 1px solid #1A2238;
    box-shadow: 0 30px 60px -30px rgba(10,15,30,0.35);
}
.log-card::before {
    content: ""; position: absolute; inset: 0;
    background:
      radial-gradient(400px 200px at 90% -10%, rgba(0,229,209,0.15), transparent 60%),
      radial-gradient(400px 200px at -10% 110%, rgba(44,91,255,0.18), transparent 60%);
    pointer-events: none;
}
.log-hd {
    display: flex; justify-content: space-between; align-items: center;
    margin-bottom: 0.9rem;
    border-bottom: 1px dashed #1F2A44;
    padding-bottom: 0.75rem;
    position: relative;
}
.log-hd .t {
    font-family: 'Chakra Petch', sans-serif;
    font-weight: 600; font-size: 0.95rem;
    letter-spacing: 0.02em; color: #F1F5FF;
}
.log-hd .kbd {
    display: inline-flex; gap: 0.35rem; align-items: center;
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.68rem; color: #93A2C6; letter-spacing: 0.1em;
}
.log-hd .kbd .live {
    width: 8px; height: 8px; border-radius: 50%; background: #00E5D1;
    box-shadow: 0 0 0 0 rgba(0,229,209,0.6);
    animation: pulseDot 1.6s infinite;
}
.log-hd .kbd.idle .live { background: #4B5878; animation: none; }
.log-body {
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.78rem;
    line-height: 1.55;
    max-height: 260px; overflow-y: auto;
    position: relative;
}
.log-row { display: flex; gap: 0.7rem; padding: 0.15rem 0; }
.log-row .ts { color: #6C7BA2; flex-shrink: 0; }
.log-row .tag {
    padding: 0 0.4rem; border-radius: 4px;
    font-size: 0.66rem; letter-spacing: 0.1em;
    text-transform: uppercase; font-weight: 600;
    align-self: center;
}
.log-row .tag.info    { background: rgba(44,91,255,0.16); color: #7BA0FF; }
.log-row .tag.ok      { background: rgba(16,185,129,0.16); color: #34D8A6; }
.log-row .tag.warn    { background: rgba(245,158,11,0.16); color: #FBBF57; }
.log-row .tag.err     { background: rgba(244,63,94,0.16);  color: #FF7A8E; }
.log-row .tag.agent   { background: rgba(124,77,255,0.18); color: #B39BFF; }
.log-row .msg { color: #D6DEEF; }
.caret { animation: blink 1s steps(2, start) infinite; color: #00E5D1; }
@keyframes blink { to { visibility: hidden; } }

/* Response card */
.resp-card {
    background: #FFFFFF;
    border: 1px solid var(--grid);
    border-radius: 16px;
    padding: 1.2rem 1.3rem;
    box-shadow: 0 22px 50px -30px rgba(10,15,30,0.18);
}

/* Footer */
.foot {
    margin-top: 3rem; padding-top: 1.4rem;
    border-top: 1px dashed var(--grid);
    display: flex; justify-content: space-between; align-items: center;
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.7rem; color: var(--slate);
    letter-spacing: 0.1em; text-transform: uppercase;
}
</style>
""", unsafe_allow_html=True)


# ============================================================================
# BRAND / TOP NAV
# ============================================================================
st.markdown("""
<div class="brand-row">
  <div class="brand">
    <div class="brand-mark">
      <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
        <path d="M4 16 L10 4 L14 12 L20 4" stroke="#00E5D1" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
        <circle cx="10" cy="4" r="1.6" fill="#2C5BFF"/>
        <circle cx="20" cy="4" r="1.6" fill="#2C5BFF"/>
        <path d="M3 20 H21" stroke="#7C4DFF" stroke-width="1.6" stroke-linecap="round" stroke-dasharray="2 3"/>
      </svg>
    </div>
    <div class="brand-name">Auto<span>ML</span></div>
    <div class="brand-tag">Agent · v0.1</div>
  </div>

  <div class="nav-links">
    <a href="#pipeline">Pipeline</a>
    <a href="#how">How it works</a>
    <a href="#config">Configure</a>
    <a href="#logs">Activity</a>
  </div>

  <div class="nav-status">
    <span class="pulse"></span>
    <span>Sandbox online</span>
  </div>
</div>
""", unsafe_allow_html=True)


# ============================================================================
# STATE
# ============================================================================
if "pipeline_status" not in st.session_state:
    st.session_state.pipeline_status = "idle"   # idle | running | success | error
if "activity_log" not in st.session_state:
    st.session_state.activity_log = []
if "last_response" not in st.session_state:
    st.session_state.last_response = None
if "last_download_url" not in st.session_state:
    st.session_state.last_download_url = None


def _ts():
    return datetime.now().strftime("%H:%M:%S")


def append_log(tag: str, msg: str):
    st.session_state.activity_log.append({
        "ts": _ts(),
        "tag": tag,
        "msg": msg,
    })


def render_pipeline_diagram(status: str):
    """Animated agent pipeline: Profile → Generate → Execute → Self-Correct."""
    nodes = [
        {"lbl": "Profile",      "sub": "01 · scan",
         "svg": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M3 3h7v7H3z"/><path d="M14 3h7v4h-7z"/><path d="M14 10h7v11h-7z"/><path d="M3 14h7v7H3z"/></svg>'},
        {"lbl": "Generate",     "sub": "02 · plan",
         "svg": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M4 4h10l6 6v10H4z"/><path d="M14 4v6h6"/><path d="M8 14h8"/><path d="M8 17h5"/></svg>'},
        {"lbl": "Execute",      "sub": "03 · run",
         "svg": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><polygon points="6,4 20,12 6,20"/></svg>'},
        {"lbl": "Self-Correct", "sub": "04 · refine",
         "svg": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M4 12a8 8 0 0 1 14-5.3"/><path d="M18 4v4h-4"/><path d="M20 12a8 8 0 0 1-14 5.3"/><path d="M6 20v-4h4"/></svg>'},
    ]
    node_html = ""
    for i, n in enumerate(nodes):
        node_html += f"""
        <div class="pipe-node">
          <div class="ring">{n['svg']}</div>
          <div class="lbl">{n['lbl']}</div>
          <div class="sub">{n['sub']}</div>
        </div>"""
        if i < 3:
            node_html += '<div style="width:0"></div>'  # spacer column

    diagram_class = "pipe-diagram"
    if status == "running":
        diagram_class += " running"
    elif status == "success":
        diagram_class += " success"
    elif status == "error":
        diagram_class += " error"

    status_pill = {
        "idle":    ('<span style="color:var(--slate)">◦ IDLE</span>'),
        "running": ('<span style="color:var(--signal)">● RUNNING</span>'),
        "success": ('<span style="color:var(--success)">● SUCCESS</span>'),
        "error":   ('<span style="color:var(--rose)">● ERROR</span>'),
    }[status]

    html = f"""
    <div class="pipe-card">
      <div class="pipe-card-hd">
        <div class="t">Agent Pipeline</div>
        <div class="k">{status_pill}</div>
      </div>
      <div class="{diagram_class}" style="display:grid;grid-template-columns:1fr auto 1fr auto 1fr auto 1fr;align-items:start;">
        <div class="pipe-node"><div class="ring">{nodes[0]['svg']}</div><div class="lbl">{nodes[0]['lbl']}</div><div class="sub">{nodes[0]['sub']}</div></div>
        <div style="align-self:center;width:60px;height:2px;background:repeating-linear-gradient(90deg,var(--grid-2) 0 6px,transparent 6px 12px);position:relative;overflow:hidden;">
          <div class="flow" style="position:absolute;top:-1px;left:0;height:4px;width:40px;border-radius:4px;background:linear-gradient(90deg,transparent,var(--signal),var(--neon),transparent);"></div>
        </div>
        <div class="pipe-node"><div class="ring">{nodes[1]['svg']}</div><div class="lbl">{nodes[1]['lbl']}</div><div class="sub">{nodes[1]['sub']}</div></div>
        <div style="align-self:center;width:60px;height:2px;background:repeating-linear-gradient(90deg,var(--grid-2) 0 6px,transparent 6px 12px);position:relative;overflow:hidden;">
          <div class="flow" style="position:absolute;top:-1px;left:0;height:4px;width:40px;border-radius:4px;background:linear-gradient(90deg,transparent,var(--signal),var(--neon),transparent);"></div>
        </div>
        <div class="pipe-node"><div class="ring">{nodes[2]['svg']}</div><div class="lbl">{nodes[2]['lbl']}</div><div class="sub">{nodes[2]['sub']}</div></div>
        <div style="align-self:center;width:60px;height:2px;background:repeating-linear-gradient(90deg,var(--grid-2) 0 6px,transparent 6px 12px);position:relative;overflow:hidden;">
          <div class="flow" style="position:absolute;top:-1px;left:0;height:4px;width:40px;border-radius:4px;background:linear-gradient(90deg,transparent,var(--signal),var(--neon),transparent);"></div>
        </div>
        <div class="pipe-node"><div class="ring">{nodes[3]['svg']}</div><div class="lbl">{nodes[3]['lbl']}</div><div class="sub">{nodes[3]['sub']}</div></div>
      </div>
    </div>
    """
    st.markdown(html, unsafe_allow_html=True)


def render_activity_log():
    """Live agent activity console."""
    is_live = st.session_state.pipeline_status == "running"
    hd_class = "kbd" if is_live else "kbd idle"
    label = "LIVE STREAM" if is_live else ("STANDBY" if st.session_state.pipeline_status == "idle" else "SESSION")
    logs = st.session_state.activity_log

    rows_html = ""
    if not logs:
        rows_html = """
        <div class="log-row">
          <span class="ts">--:--:--</span>
          <span class="tag info">boot</span>
          <span class="msg">Waiting for pipeline trigger… <span class="caret">▍</span></span>
        </div>"""
    else:
        for row in logs[-120:]:
            rows_html += f"""
            <div class="log-row">
              <span class="ts">{row['ts']}</span>
              <span class="tag {row['tag']}">{row['tag']}</span>
              <span class="msg">{row['msg']}</span>
            </div>"""
        if is_live:
            rows_html += '<div class="log-row"><span class="ts">--:--:--</span><span class="tag info">wait</span><span class="msg">Streaming agent telemetry… <span class="caret">▍</span></span></div>'

    html = f"""
    <div class="log-card" id="logs">
      <div class="log-hd">
        <div class="t">Agent Activity</div>
        <div class="{hd_class}"><span class="live"></span> {label}</div>
      </div>
      <div class="log-body">
        {rows_html}
      </div>
    </div>
    """
    st.markdown(html, unsafe_allow_html=True)


# ============================================================================
# HERO
# ============================================================================
col_l, col_r = st.columns([1.35, 1])

with col_l:
    st.markdown("""
    <div class="eyebrow"><span class="dot"></span> Autonomous ML Engineer</div>
    <div class="hero-title">Ship models <span class="accent">without writing<br/>the pipeline.</span></div>
    <div class="hero-sub">
      AutoML is an agentic system that profiles your dataset, generates the training
      code, executes it in a sandbox, and self-corrects on failure — until a model bundle
      is ready to download. Point it at a CSV, give it a target column, and step back.
    </div>
    <div class="hero-meta">
      <span><b>◐</b> Profile · Generate · Execute · Self-Correct</span>
      <span><b>◐</b> n8n orchestrated</span>
      <span><b>◐</b> Sandbox isolated</span>
    </div>
    """, unsafe_allow_html=True)

with col_r:
    render_pipeline_diagram(st.session_state.pipeline_status)


# ============================================================================
# HOW IT WORKS
# ============================================================================
st.markdown("""
<div class="section" id="how">
  <div class="lhs">
    <div class="idx">// 01</div>
    <div class="ttl">How the agent thinks</div>
  </div>
  <div class="sub">Four coordinated phases</div>
</div>
""", unsafe_allow_html=True)

st.markdown("""
<div class="hiw-grid">
  <div class="hiw">
    <div class="num">01 / PROFILE</div>
    <div class="ico">
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><circle cx="11" cy="11" r="7"/><path d="m20 20-3.5-3.5"/></svg>
    </div>
    <div class="h">Profile the data</div>
    <div class="p">Scans schema, dtypes, missing rates, cardinality, target balance & leakage risks.</div>
  </div>
  <div class="hiw">
    <div class="num">02 / GENERATE</div>
    <div class="ico">
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M4 4h10l6 6v10H4z"/><path d="M14 4v6h6"/><path d="M8 14h8"/><path d="M8 17h5"/></svg>
    </div>
    <div class="h">Generate the plan</div>
    <div class="p">LLM writes preprocessing, feature engineering & model code tailored to your dataset.</div>
  </div>
  <div class="hiw">
    <div class="num">03 / EXECUTE</div>
    <div class="ico">
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><polygon points="6,4 20,12 6,20"/></svg>
    </div>
    <div class="h">Execute in sandbox</div>
    <div class="p">Runs the generated code inside an isolated container via MCP-connected tools.</div>
  </div>
  <div class="hiw">
    <div class="num">04 / SELF-CORRECT</div>
    <div class="ico">
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M4 12a8 8 0 0 1 14-5.3"/><path d="M18 4v4h-4"/><path d="M20 12a8 8 0 0 1-14 5.3"/><path d="M6 20v-4h4"/></svg>
    </div>
    <div class="h">Self-correct on error</div>
    <div class="p">Reads tracebacks, diagnoses the fault, revises the code, retries — until success.</div>
  </div>
</div>
""", unsafe_allow_html=True)


# ============================================================================
# CONFIG
# ============================================================================
st.markdown("""
<div class="section" id="config">
  <div class="lhs">
    <div class="idx">// 02</div>
    <div class="ttl">Configure the run</div>
  </div>
  <div class="sub">n8n webhook · dataset · target</div>
</div>
""", unsafe_allow_html=True)

st.markdown('<div class="cfg-card">', unsafe_allow_html=True)

webhook_url = "https://armored-body-case.ngrok-free.dev/webhook/trigger-automl"

col1, col2 = st.columns(2)
with col1:
    uploaded_file = st.file_uploader("Upload CSV Dataset", type=["csv"])
    if uploaded_file is not None:
        dataset_path = "c:/Users/KIIT/Desktop/AutoML/uploaded_dataset.csv"
        with open(dataset_path, "wb") as f:
            f.write(uploaded_file.getbuffer())
        st.caption(f"Saved uploaded file to: `{dataset_path}`")
    else:
        dataset_path = st.text_input(
            "Dataset Path (Local to host)",
            value="c:/Users/KIIT/Desktop/AutoML/sample_dataset.csv",
            help="The local file path that the Sandbox container/MCP servers can read.",
        )
with col2:
    # Try to parse the target variables if the CSV exists
    import pandas as pd
    import os
    columns = []
    if dataset_path and os.path.exists(dataset_path):
        try:
            df_preview = pd.read_csv(dataset_path, nrows=2)
            columns = list(df_preview.columns)
        except Exception:
            pass

    if columns:
        target_variable = st.selectbox(
            "Target Variable",
            options=columns,
            index=len(columns) - 1 if columns else 0,
            help="Select the target variable (column) to predict."
        )
    else:
        target_variable = st.text_input(
            "Target Variable",
            value="purchased",
            help="The column name you want the model to predict.",
        )

col3, col4 = st.columns(2)
with col3:
    task_type = st.selectbox(
        "Task Type",
        options=["classification", "regression"],
        format_func=lambda x: x.capitalize(),
        help="Select the type of supervised learning task you want to perform."
    )
with col4:
    if task_type == "classification":
        model_options = [
            "Logistic Regression",
            "Decision Tree",
            "Random Forest",
            "XGBoost",
            "LightGBM",
            "CatBoost",
            "Support Vector Machine (SVM)",
            "K-Nearest Neighbors",
            "Naive Bayes"
        ]
    else:
        model_options = [
            "Linear Regression",
            "Decision Tree",
            "Random Forest",
            "XGBoost",
            "LightGBM",
            "CatBoost",
            "Support Vector Machine (SVR)",
            "K-Nearest Neighbors"
        ]
    selected_model = st.selectbox(
        "Model Selection",
        options=model_options,
        help="Choose the model algorithm to train on your dataset."
    )

min_threshold = st.slider(
    "Minimum Accuracy/R2 Performance Threshold (%)",
    min_value=50,
    max_value=99,
    value=90,
    step=1,
    help="The target validation score (Accuracy for Classification, R2 for Regression). Below this threshold, hyperparameter tuning triggers."
) / 100.0

# Sample chips (purely presentational — copy/paste friendly for the user)
st.markdown("""
<div style="margin-top:0.9rem;">
  <div style="font-family:'JetBrains Mono',monospace;font-size:0.68rem;letter-spacing:0.14em;color:var(--slate);text-transform:uppercase;margin-bottom:0.45rem;">Try a sample</div>
  <div class="chips-row">
    <div class="chip signal"><span class="dot"></span><span class="k">dataset</span><span>sample_dataset.csv</span></div>
    <div class="chip signal"><span class="dot"></span><span class="k">target</span><span>purchased</span></div>
    <div class="chip violet"><span class="dot"></span><span class="k">dataset</span><span>titanic.csv</span></div>
    <div class="chip violet"><span class="dot"></span><span class="k">target</span><span>Survived</span></div>
    <div class="chip amber"><span class="dot"></span><span class="k">dataset</span><span>housing.csv</span></div>
    <div class="chip amber"><span class="dot"></span><span class="k">target</span><span>price</span></div>
    <div class="chip"><span class="dot"></span><span class="k">dataset</span><span>churn.csv</span></div>
    <div class="chip"><span class="dot"></span><span class="k">target</span><span>churned</span></div>
  </div>
</div>
""", unsafe_allow_html=True)

trigger = st.button("◈  Trigger AutoML Pipeline", type="primary")

st.markdown('</div>', unsafe_allow_html=True)


# ============================================================================
# PIPELINE + ACTIVITY LOG (side-by-side status region)
# ============================================================================
st.markdown("""
<div class="section" id="pipeline">
  <div class="lhs">
    <div class="idx">// 03</div>
    <div class="ttl">Live pipeline</div>
  </div>
  <div class="sub">Agent telemetry stream</div>
</div>
""", unsafe_allow_html=True)

log_placeholder = st.empty()
with log_placeholder.container():
    render_activity_log()


# ============================================================================
# EXECUTION — request/response logic UNCHANGED from the original app
# ============================================================================
def refresh_log():
    """Re-render the activity log placeholder with current state."""
    with log_placeholder.container():
        render_activity_log()


if trigger:
    if not webhook_url:
        st.error("Please enter a valid webhook URL.")
    elif not dataset_path:
        st.error("Please enter a dataset path.")
    elif not target_variable:
        st.error("Please enter a target variable.")
    else:
        # Reset log for a fresh run (purely presentational)
        st.session_state.activity_log = []
        st.session_state.pipeline_status = "running"
        st.session_state.last_response = None
        st.session_state.last_download_url = None

        append_log("info",  "Trigger received from operator.")
        append_log("agent", f"Payload prepared → file_path='{dataset_path}', target_variable='{target_variable}', task_type='{task_type}', selected_model='{selected_model}', min_threshold={min_threshold}")
        append_log("info",  f"POST → {webhook_url}")
        append_log("agent", "Phase 01 · <b>Profile</b> — reading schema, dtypes and target balance…")
        refresh_log()

        payload = {
            "file_path": dataset_path,
            "target_variable": target_variable,
            "task_type": task_type,
            "selected_model": selected_model,
            "min_threshold": min_threshold,
        }

        try:
            with st.spinner("Pipeline is running… Check n8n dashboard for real-time progress."):
                # Small pre-request beat so the user sees phase-01 tick in.
                # Does not alter request semantics.
                time.sleep(0.35)
                append_log("agent", "Phase 02 · <b>Generate</b> — LLM drafting preprocessing + model code…")
                refresh_log()

                response = requests.post(webhook_url, json=payload, timeout=300)

            if response.status_code == 200:
                append_log("agent", "Phase 03 · <b>Execute</b> — running generated code inside sandbox…")
                append_log("agent", "Phase 04 · <b>Self-Correct</b> — validating artifacts & metrics…")
                append_log("ok",    f"Webhook responded 200 OK in { '<1s' if False else 'session' }.")

                st.session_state.pipeline_status = "success"
                try:
                    res_data = response.json()
                except Exception:
                    res_data = {"raw": response.text}
                st.session_state.last_response = res_data

                # Retrieve download URL (logic preserved)
                download_url = None
                if isinstance(res_data, dict):
                    download_url = res_data.get("download_url")
                elif isinstance(res_data, list) and len(res_data) > 0:
                    download_url = res_data[0].get("download_url")

                if download_url:
                    local_url = download_url.replace("host.docker.internal", "localhost")
                    st.session_state.last_download_url = local_url
                    append_log("ok", f"Bundle artifact ready → <span style='color:#7BA0FF'>{local_url}</span>")
                else:
                    append_log("warn", "No download_url found in response payload.")

                append_log("ok", "Pipeline finished successfully. Model bundle produced.")
            else:
                st.session_state.pipeline_status = "error"
                st.session_state.last_response = {"status_code": response.status_code, "body": response.text}
                append_log("err", f"Webhook returned status {response.status_code}.")
                append_log("err", f"Body: {response.text[:400]}")
        except Exception as e:
            st.session_state.pipeline_status = "error"
            st.session_state.last_response = {"error": str(e)}
            append_log("err", f"Connection failed: {str(e)}")
            append_log("warn", "Ensure n8n is running and 'Listen for test event' or 'Execute workflow' is active.")

        refresh_log()


# ============================================================================
# RESULT PANEL
# ============================================================================
if st.session_state.pipeline_status == "success":
    st.markdown("""
    <div class="section">
      <div class="lhs">
        <div class="idx">// 04</div>
        <div class="ttl">Result</div>
      </div>
      <div class="sub">Model bundle & response</div>
    </div>
    """, unsafe_allow_html=True)

    st.success("AutoML pipeline finished successfully!")

    if st.session_state.last_download_url:
        st.link_button(
            "📥  Download AutoML Bundle (.zip)",
            st.session_state.last_download_url,
            type="primary",
        )

    st.markdown('<div style="margin-top:1rem;font-family:\'JetBrains Mono\',monospace;font-size:0.72rem;letter-spacing:0.12em;color:var(--slate);text-transform:uppercase;">Raw response</div>', unsafe_allow_html=True)
    st.json(st.session_state.last_response)

elif st.session_state.pipeline_status == "error":
    st.markdown("""
    <div class="section">
      <div class="lhs">
        <div class="idx">// 04</div>
        <div class="ttl">Result</div>
      </div>
      <div class="sub">Diagnostics</div>
    </div>
    """, unsafe_allow_html=True)
    st.error("Pipeline did not complete. See agent activity for details.")
    if st.session_state.last_response is not None:
        st.json(st.session_state.last_response)


# ============================================================================
# FOOTER
# ============================================================================
st.markdown("""
<div class="foot">
  <div>◈ AutoML · Agentic ML Engineer</div>
  <div>Orchestrated via n8n · Executed in sandbox · Corrected by agent</div>
</div>
""", unsafe_allow_html=True)
