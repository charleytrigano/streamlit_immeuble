import streamlit as st
from supabase import create_client

# ----------------------------------
# CONFIG STREAMLIT
# ----------------------------------
st.set_page_config(
    page_title="Pilotage des charges",
    layout="wide",
)

# ----------------------------------
# CONNEXION SUPABASE
# ----------------------------------
SUPABASE_URL = st.secrets["SUPABASE_URL"]
SUPABASE_KEY = st.secrets["SUPABASE_KEY"]

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# ----------------------------------
# IMPORT DES ONGLET UI
# ----------------------------------
from utils.depenses_ui import depenses_ui
from utils.budget_ui import budget_ui
from utils.budget_vs_reel_ui import budget_vs_reel_ui
from utils.statistiques_ui import statistiques_ui
from utils.repartition_lots_ui import repartition_lots_ui

# ----------------------------------
# SIDEBAR
# ----------------------------------
st.sidebar.title("📊 Pilotage des charges")

page = st.sidebar.radio(
    "Navigation",
    [
        "État des dépenses",
        "Budget",
        "Budget vs Réel",
        "Statistiques",
        "Répartition par lots",
    ],
)

st.sidebar.markdown("---")
st.sidebar.caption("Immeuble • Gestion & Analyse")

# ----------------------------------
# ROUTING
# ----------------------------------
if page == "État des dépenses":
    depenses_ui(supabase)

elif page == "Budget":
    budget_ui(supabase)

elif page == "Budget vs Réel":
    budget_vs_reel_ui(supabase)

elif page == "Statistiques":
    statistiques_ui(supabase)

elif page == "Répartition par lots":
    repartition_lots_ui(supabase)