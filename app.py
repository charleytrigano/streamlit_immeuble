import sys
import os
import streamlit as st

# =========================
# FIX PYTHONPATH (CRITIQUE)
# =========================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

UTILS_DIR = os.path.join(BASE_DIR, "utils")
if UTILS_DIR not in sys.path:
    sys.path.insert(0, UTILS_DIR)

# =========================
# CONFIG STREAMLIT
# =========================
st.set_page_config(
    page_title="Pilotage Immeuble",
    page_icon="🏢",
    layout="wide",
)

# =========================
# SUPABASE
# =========================
from supabase_client import get_supabase_client

@st.cache_resource
def init_supabase():
    return get_supabase_client()

supabase = init_supabase()

# =========================
# IMPORT UI (SAFE)
# =========================
try:
    from utils.depenses_ui import depenses_ui
    from utils.budget_ui import budget_ui
    from utils.plan_comptable_ui import plan_comptable_ui
    from utils.lots_ui import lots_ui
    from utils.repartition_lots_ui import repartition_lots_ui
    from utils.controle_repartition_ui import controle_repartition_ui
    from utils.charges_par_lot_ui import charges_par_lot_ui
    from utils.appels_fonds_trimestre_ui import appels_fonds_trimestre_ui
    from utils.statistiques_ui import statistiques_ui
except Exception as e:
    st.error("❌ Erreur d'import des modules UI")
    st.exception(e)
    st.stop()

# =========================
# SIDEBAR
# =========================
st.sidebar.title("🏢 Pilotage immeuble")

annee = st.sidebar.selectbox(
    "Année",
    [2024, 2025, 2026],
    index=1
)

menu = st.sidebar.radio(
    "Navigation",
    [
        "Dépenses",
        "Budgets",
        "Plan comptable",
        "Lots",
        "Répartition par lot",
        "Contrôle répartition",
        "Charges par lot",
        "Appels de fonds trimestriels",
        "Statistiques",
    ]
)

# =========================
# ROUTING
# =========================
if menu == "Dépenses":
    depenses_ui(supabase, annee)

elif menu == "Budgets":
    budget_ui(supabase, annee)

elif menu == "Plan comptable":
    plan_comptable_ui(supabase)

elif menu == "Lots":
    lots_ui(supabase)

elif menu == "Répartition par lot":
    repartition_lots_ui(supabase, annee)

elif menu == "Contrôle répartition":
    controle_repartition_ui(supabase, annee)

elif menu == "Charges par lot":
    charges_par_lot_ui(supabase, annee)

elif menu == "Appels de fonds trimestriels":
    appels_fonds_trimestre_ui(supabase, annee)

elif menu == "Statistiques":
    statistiques_ui(supabase, annee)