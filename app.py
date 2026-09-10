"""
Disease Protein Discovery Platform
===================================
Run:  python3 -m streamlit run app.py
"""

import streamlit as st

st.set_page_config(
    page_title="Disease Protein Discovery",
    page_icon="🧬",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Custom CSS for consistent styling ────────────────────────────────────

st.markdown("""
<style>
    .block-container { padding-top: 1.5rem; }
    [data-testid="stSidebar"] { min-width: 260px; max-width: 300px; }
    [data-testid="stMetric"] { background: #f8f9fa; padding: 12px 16px;
        border-radius: 8px; border-left: 4px solid #2196F3; }
    [data-testid="stMetricValue"] { font-size: 1.3rem; }
    div[data-testid="stExpander"] details summary p { font-weight: 600; }
</style>
""", unsafe_allow_html=True)

# ── Page registry (5 pages) ─────────────────────────────────────────────

PAGES = [
    ("🏠  Home",              "home"),
    ("🧬  Disease Explorer",  "disease_explorer"),
    ("🔬  Protein Explorer",  "protein_explorer"),
    ("📊  Model Analysis",    "model_comparison"),
    ("📖  Methodology",       "methodology"),
]

# ── Sidebar ──────────────────────────────────────────────────────────────

st.sidebar.markdown(
    "<h2 style='margin-bottom:0; font-size:1.3rem'>🧬 Disease Protein<br>Discovery Platform</h2>",
    unsafe_allow_html=True,
)
st.sidebar.caption("Network-based candidate protein prioritization")
st.sidebar.divider()

nav_from_session = st.session_state.get("nav")
page_names = [name for name, _ in PAGES]
default_idx = 0
if nav_from_session:
    for i, (name, _) in enumerate(PAGES):
        if nav_from_session in name:
            default_idx = i
            break
    if "nav" in st.session_state:
        del st.session_state["nav"]

selection = st.sidebar.radio(
    "Navigate", page_names,
    index=default_idx,
    label_visibility="collapsed",
)

st.sidebar.divider()

st.sidebar.markdown(
    "**PPI Network**  \n"
    "21,557 proteins · 342,353 interactions  \n\n"
    "**Diseases:** 519 (≥10 genes each)  \n"
    "**Methods:** 5 prediction algorithms  \n"
    "**Orbits:** 73 graphlet positions  \n\n"
    "[SNAP Data](https://snap.stanford.edu/pathways/) · "
    "[Paper](https://cs.stanford.edu/people/jure/pubs/pathways-psb18.pdf)"
)

st.sidebar.divider()
st.sidebar.caption(
    "Predictions are for research purposes only and should not "
    "be interpreted as clinical diagnoses."
)

# ── Route to selected page ───────────────────────────────────────────────

page_map = dict(PAGES)
module_name = page_map[selection]

if module_name == "home":
    from app.pages.home import render
elif module_name == "disease_explorer":
    from app.pages.disease_explorer import render
elif module_name == "protein_explorer":
    from app.pages.protein_explorer import render
elif module_name == "model_comparison":
    from app.pages.model_comparison import render
elif module_name == "methodology":
    from app.pages.methodology import render

render()
