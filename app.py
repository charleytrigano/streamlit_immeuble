import sys
from pathlib import Path

# ======================================================
# PATH (pour utils/)
# ======================================================
ROOT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT_DIR))

# ======================================================
# IMPORTS
# ======================================================
import streamlit as st
from supabase import create_client

from utils.depenses_ui import depenses_ui
from utils.budget_ui import budget_ui
from utils.budget_vs_reel_ui import budget_vs_reel_ui
from utils.controle_repartition_ui import controle_repartition_ui
from utils.charges_par_lot_ui import charges_par_lot_ui

# ======================================================
# CONFIG STREAMLIT
# ======================================================
st.set_page_config(
    page_title="Pilotage des charges de l’immeuble",
    layout="wide",
)

st.title("🏢 Pilotage des charges de l’immeuble")

# ======================================================
# CONNEXION SUPABASE
# ======================================================
SUPABASE_URL = st.secrets["SUPABASE_URL"]
SUPABASE_KEY = st.secrets["SUPABASE_KEY"]

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# ======================================================
# SIDEBAR — NAVIGATION
# ======================================================
st.sidebar.title("Navigation")

page = st.sidebar.radio(
    "Aller à",
    [
        "📋 État des dépenses",
        "💰 Budget",
        "📊 Budget vs Réel",
        "📐 Contrôle répartition",
        "🏠 Charges par lot",
    ],
)

# ======================================================
# ROUTAGE DES PAGES
# ======================================================
if page == "📋 État des dépenses":
    depenses_ui(supabase)

elif page == "💰 Budget":
    budget_ui(supabase)

elif page == "📊 Budget vs Réel":
    budget_vs_reel_ui(supabase)

elif page == "📐 Contrôle répartition":
    controle_repartition_ui(supabase)

elif page == "🏠 Charges par lot":
    charges_par_lot_ui(supabase)