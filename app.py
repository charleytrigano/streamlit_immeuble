import streamlit as st

# =========================
# CONFIG
# =========================
st.set_page_config(
    page_title="Pilotage des charges de l’immeuble",
    layout="wide",
)

# =========================
# SUPABASE
# =========================
from utils.supabase_client import get_supabase
supabase = get_supabase()

# =========================
# UI IMPORTS
# =========================
from utils.budget_ui import budget_ui
from utils.depenses_ui import depenses_ui
from utils.budget_vs_reel_ui import budget_vs_reel_ui

# =========================
# SIDEBAR
# =========================
st.sidebar.title("Navigation")

page = st.sidebar.radio(
    "Aller à",
    [
        "📋 État des dépenses",
        "💰 Budget",
        "📊 Budget vs Réel",
    ]
)

# =========================
# ROUTAGE
# =========================
if page == "📋 État des dépenses":
    depenses_ui(supabase)

elif page == "💰 Budget":
    budget_ui(supabase)

elif page == "📊 Budget vs Réel":
    budget_vs_reel_ui(supabase)