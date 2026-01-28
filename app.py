import streamlit as st
from supabase import create_client

# =========================
# CONFIG GÉNÉRALE
# =========================
st.set_page_config(
    page_title="Immeuble – Pilotage",
    layout="wide",
    initial_sidebar_state="collapsed"
)

st.title("🏢 Pilotage de l’immeuble")

# =========================
# SUPABASE
# =========================
SUPABASE_URL = st.secrets["supabase"]["url"]
SUPABASE_KEY = st.secrets["supabase"]["key"]

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# =========================
# IMPORT DES UI
# =========================
from utils.depenses_ui import depenses_ui
from utils.budgets_ui import budgets_ui
from utils.plan_comptable_ui import plan_comptable_ui
from utils.lots_ui import lots_ui

# =========================
# ONGLET PRINCIPAL
# =========================
tab_depenses, tab_budgets, tab_plan, tab_lots = st.tabs([
    "📄 Dépenses",
    "💰 Budgets",
    "📘 Plan comptable",
    "🏢 Lots"
])

# =========================
# DÉPENSES
# =========================
with tab_depenses:
    depenses_ui(supabase)

# =========================
# BUDGETS
# =========================
with tab_budgets:
    budgets_ui(supabase)

# =========================
# PLAN COMPTABLE
# =========================
with tab_plan:
    plan_comptable_ui(supabase)

# =========================
# LOTS
# =========================
with tab_lots:
    lots_ui(supabase)

# =========================
# FOOTER
# =========================
st.divider()
st.caption(
    "Immeuble – Pilotage | "
    "Données sécurisées | "
    "Structure stable | "
    "Sans suppression non maîtrisée"
)