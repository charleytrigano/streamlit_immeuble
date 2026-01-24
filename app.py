import streamlit as st
from supabase import create_client

from utils.budget_vs_reel_ui import budget_vs_reel_ui
from utils.statistiques_ui import statistiques_ui
from utils.controle_repartition_ui import controle_repartition_ui

# -------------------------
# Configuration Supabase
# -------------------------
SUPABASE_URL = st.secrets["SUPABASE_URL"]
SUPABASE_KEY = st.secrets["SUPABASE_KEY"]

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# -------------------------
# Navigation
# -------------------------
st.sidebar.title("📊 Pilotage immeuble")

page = st.sidebar.radio(
    "Navigation",
    [
        "Statistiques",
        "Budget vs Réel",
        "Contrôle répartition"
    ]
)

# -------------------------
# Pages
# -------------------------
if page == "Statistiques":
    statistiques_ui(supabase)

elif page == "Budget vs Réel":
    budget_vs_reel_ui(supabase)

elif page == "Contrôle répartition":
    controle_repartition_ui(supabase)