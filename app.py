import streamlit as st
from config import get_supabase_client

# UI modules (TOUS À LA RACINE)
from depenses_ui import depenses_ui
from budget_ui import budget_ui
from lots_ui import lots_ui
from repartition_lots_ui import repartition_lots_ui
from charges_par_lot_ui import charges_par_lot_ui
from appels_fonds_trimestre_ui import appels_fonds_trimestre_ui
from controle_repartition_ui import controle_repartition_ui
from plan_comptable_ui import plan_comptable_ui


# -----------------------------
# App init
# -----------------------------
st.set_page_config(page_title="Gestion immeuble", layout="wide")
st.success("🚀 app.py chargé correctement")

supabase = get_supabase_client()

# -----------------------------
# Sidebar
# -----------------------------
st.sidebar.title("📂 Navigation")

annee = st.sidebar.selectbox(
    "Année",
    [2023, 2024, 2025, 2026],
    index=1
)

onglet = st.sidebar.radio(
    "Module",
    [
        "Dépenses",
        "Budget",
        "Lots",
        "Répartition des lots",
        "Charges par lot",
        "Appels de fonds trimestriels",
        "Contrôle répartition",
        "Plan comptable",
    ]
)

# -----------------------------
# Routing
# -----------------------------
if onglet == "Dépenses":
    depenses_ui(supabase, annee)

elif onglet == "Budget":
    budget_ui(supabase, annee)

elif onglet == "Lots":
    lots_ui(supabase)

elif onglet == "Répartition des lots":
    repartition_lots_ui(supabase)

elif onglet == "Charges par lot":
    charges_par_lot_ui(supabase, annee)

elif onglet == "Appels de fonds trimestriels":
    appels_fonds_trimestre_ui(supabase, annee)

elif onglet == "Contrôle répartition":
    controle_repartition_ui(supabase)

elif onglet == "Plan comptable":
    plan_comptable_ui(supabase)