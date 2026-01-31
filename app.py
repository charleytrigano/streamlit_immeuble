import os
import sys

# =====================================================
# 🔧 PYTHONPATH FIX (OBLIGATOIRE STREAMLIT CLOUD)
# =====================================================
ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
UTILS_DIR = os.path.join(ROOT_DIR, "utils")

if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

if UTILS_DIR not in sys.path:
    sys.path.insert(0, UTILS_DIR)

# =====================================================
# IMPORTS
# =====================================================
import streamlit as st

from utils.supabase_client import get_supabase_client

from budget_ui import budget_ui
from depenses_ui import depenses_ui
from plan_comptable_ui import plan_comptable_ui
from lots_ui import lots_ui
from repartition_lots_ui import repartition_lots_ui
from charges_par_lot_ui import charges_par_lot_ui
from controle_repartition_ui import controle_repartition_ui
from appels_fonds_trimestre_ui import appels_fonds_trimestre_ui
from statistiques_ui import statistiques_ui

# =====================================================
# STREAMLIT CONFIG
# =====================================================
st.set_page_config(
    page_title="🏢 Pilotage Immeuble",
    page_icon="🏢",
    layout="wide"
)

# =====================================================
# SUPABASE
# =====================================================
@st.cache_resource
def init_supabase():
    return get_supabase_client()

# =====================================================
# MAIN
# =====================================================
def main():
    st.title("🏢 Pilotage de l’immeuble")

    supabase = init_supabase()

    st.sidebar.header("Paramètres")
    annee = st.sidebar.selectbox("Année", [2024, 2025, 2026], index=1)

    menu = st.sidebar.radio(
        "Navigation",
        [
            "Budgets",
            "Dépenses",
            "Plan comptable",
            "Lots",
            "Répartition par lot",
            "Charges par lot",
            "Contrôle répartition",
            "Appels de fonds trimestriels",
            "Statistiques",
        ]
    )

    if menu == "Budgets":
        budget_ui(supabase, annee)

    elif menu == "Dépenses":
        depenses_ui(supabase, annee)

    elif menu == "Plan comptable":
        plan_comptable_ui(supabase)

    elif menu == "Lots":
        lots_ui(supabase)

    elif menu == "Répartition par lot":
        repartition_lots_ui(supabase, annee)

    elif menu == "Charges par lot":
        charges_par_lot_ui(supabase, annee)

    elif menu == "Contrôle répartition":
        controle_repartition_ui(supabase, annee)

    elif menu == "Appels de fonds trimestriels":
        appels_fonds_trimestre_ui(supabase, annee)

    elif menu == "Statistiques":
        statistiques_ui(supabase, annee)

# =====================================================
# ENTRYPOINT
# =====================================================
if __name__ == "__main__":
    main()