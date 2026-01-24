import streamlit as st

# ======================================================
# CONFIG STREAMLIT
# ======================================================
st.set_page_config(
    page_title="Pilotage des charges de l’immeuble",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.title("🏢 Pilotage des charges de l’immeuble")

# ======================================================
# SUPABASE
# ======================================================
from utils.supabase_client import get_supabase

supabase = get_supabase()

# ======================================================
# IMPORT UI
# ======================================================
from utils.depenses_ui import depenses_ui
from utils.budget_ui import budget_ui
from utils.budget_vs_reel_ui import budget_vs_reel_ui
from utils.statistiques_ui import statistiques_ui

# ======================================================
# SIDEBAR — NAVIGATION
# ======================================================
st.sidebar.title("Navigation")

menu = st.sidebar.radio(
    "Aller à",
    [
        "📋 État des dépenses",
        "💰 Budget",
        "📊 Budget vs Réel",
        "📈 Statistiques",
    ],
)

# ======================================================
# ROUTAGE
# ======================================================
if menu == "📋 État des dépenses":
    depenses_ui(supabase)

elif menu == "💰 Budget":
    budget_ui(supabase)

elif menu == "📊 Budget vs Réel":
    budget_vs_reel_ui(supabase)

elif menu == "📈 Statistiques":
    statistiques_ui(supabase)