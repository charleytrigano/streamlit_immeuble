import streamlit as st

import sys
import os

sys.path.append(os.path.dirname(__file__))

from supabase import create_client
from utils.depenses_ui import depenses_ui
from utils.budgets_ui import budgets_ui
from utils.plan_comptable_ui import plan_comptable_ui
from utils.repartition_ui import repartition_par_lot_ui, controle_repartition_ui





# --------------------------------------------------
# CONFIG
# --------------------------------------------------
st.set_page_config(
    page_title="Pilotage des charges",
    layout="wide"
)

# --------------------------------------------------
# SUPABASE (ANON KEY)
# --------------------------------------------------
SUPABASE_URL = st.secrets["SUPABASE_URL"]
SUPABASE_ANON_KEY = st.secrets["SUPABASE_ANON_KEY"]

supabase = create_client(SUPABASE_URL, SUPABASE_ANON_KEY)

# --------------------------------------------------
# SIDEBAR
# --------------------------------------------------
st.sidebar.title("📊 Pilotage immeuble")

annee = st.sidebar.selectbox(
    "Année",
    [2023, 2024, 2025],
    index=2
)

page = st.sidebar.radio(
    "Menu",
    [
        "📄 Dépenses",
        "💰 Budgets",
        "📘 Plan comptable",
        "📊 Répartition par lot",
        "✅ Contrôle"
    ]
)

# --------------------------------------------------
# ROUTING
# --------------------------------------------------
if page == "📄 Dépenses":
    depenses_ui(supabase, annee)

elif page == "💰 Budgets":
    budgets_ui(supabase, annee)

elif page == "📘 Plan comptable":
    plan_comptable_ui(supabase)

elif page == "📊 Répartition par lot":
    repartition_par_lot_ui(supabase, annee)

elif page == "✅ Contrôle":
    controle_repartition_ui(supabase, annee)