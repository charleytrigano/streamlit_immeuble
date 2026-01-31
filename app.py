import streamlit as st

# =========================
# CONFIG STREAMLIT
# =========================
st.set_page_config(
    page_title="Pilotage Immeuble",
    page_icon="🏢",
    layout="wide",
)

# =========================
# IMPORT SUPABASE
# =========================
from supabase_client import get_supabase_client

# =========================
# IMPORT DES UI
# =========================
from utils.depenses_ui import depenses_ui
from utils.budget_ui import budget_ui
from utils.plan_comptable_ui import plan_comptable_ui
from utils.lots_ui import lots_ui
from utils.repartition_lots_ui import repartition_lots_ui
from utils.controle_repartition_ui import controle_repartition_ui
from utils.charges_par_lot_ui import charges_par_lot_ui
from utils.appels_fonds_trimestre_ui import appels_fonds_trimestre_ui
from utils.statistiques_ui import statistiques_ui

# =========================
# INIT SUPABASE
# =========================
@st.cache_resource
def init_supabase():
    return get_supabase_client()

supabase = init_supabase()

# =========================
# SIDEBAR
# =========================
st.sidebar.title("🏢 Pilotage immeuble")

annee = st.sidebar.selectbox(
    "Année",
    options=[2024, 2025, 2026],
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
# ROUTAGE
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