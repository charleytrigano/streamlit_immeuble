import streamlit as st
from supabase import create_client

from utils.depenses_ui import depenses_ui
from utils.budget_ui import budget_ui          # 👈 retour du module Budget
from utils.plan_comptable_ui import plan_comptable_ui
from utils.lots_ui import lots_ui
from utils.repartition_lots_ui import repartition_lots_ui
from utils.appels_fonds_trimestre_ui import appels_fonds_trimestre_ui


# =========================
# CONFIG STREAMLIT
# =========================
st.set_page_config(
    page_title="Immeuble – Pilotage",
    layout="wide"
)

st.title("🏢 Pilotage des charges de l’immeuble")


# =========================
# CONNEXION SUPABASE (ANON)
# =========================
SUPABASE_URL = st.secrets["SUPABASE_URL"]
SUPABASE_KEY = st.secrets["SUPABASE_ANON_KEY"]   # 👈 plus de service role ici

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)


# =========================
# SIDEBAR
# =========================
st.sidebar.header("⚙️ Paramètres")

annee = st.sidebar.selectbox(
    "Année",
    options=[2024, 2025, 2026],
    index=1,
)

onglet = st.sidebar.radio(
    "Navigation",
    [
        "Dépenses",
        "Budget",
        "Appels de fonds trimestriels",
        "Répartition par lot",
        "Plan comptable",
        "Lots",
    ]
)


# =========================
# ROUTAGE
# =========================
if onglet == "Dépenses":
    depenses_ui(supabase, annee)

elif onglet == "Budget":
    budgets_ui(supabase, annee)

elif onglet == "Appels de fonds trimestriels":
    appels_fonds_trimestre_ui(supabase, annee)

elif onglet == "Répartition par lot":
    repartition_lots_ui(supabase, annee)

elif onglet == "Plan comptable":
    plan_comptable_ui(supabase)

elif onglet == "Lots":
    lots_ui(supabase)


# =========================
# FOOTER
# =========================
st.markdown("---")
st.caption("Immeuble – Pilotage | Budgets, charges & appels de fonds")
