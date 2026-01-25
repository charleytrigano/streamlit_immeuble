import sys
from pathlib import Path

# -------------------------------------------------
# Gestion du path pour importer utils/
# -------------------------------------------------
ROOT_DIR = Path(__file__).resolve().parent
sys.path.append(str(ROOT_DIR))

# -------------------------------------------------
# Imports standards
# -------------------------------------------------
import streamlit as st
from supabase import create_client

# -------------------------------------------------
# Imports UI
# -------------------------------------------------
from utils.depenses_ui import depenses_ui
from utils.budget_ui import budget_ui
from utils.budget_vs_reel_ui import budget_vs_reel_ui
from utils.controle_repartition_ui import controle_repartition_ui

# -------------------------------------------------
# Configuration Streamlit
# -------------------------------------------------
st.set_page_config(
    page_title="Pilotage des charges",
    layout="wide"
)

# -------------------------------------------------
# Connexion Supabase
# -------------------------------------------------
SUPABASE_URL = st.secrets["SUPABASE_URL"]
SUPABASE_KEY = st.secrets["SUPABASE_KEY"]

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# -------------------------------------------------
# Menu principal
# -------------------------------------------------
st.sidebar.title("📊 Pilotage des charges")

menu = st.sidebar.radio(
    "Navigation",
    [
        "Dépenses",
        "Budget",
        "Budget vs Réel",
        "Contrôle répartition",
    ]
)

# -------------------------------------------------
# Routing
# -------------------------------------------------
if menu == "Dépenses":
    depenses_ui(supabase)

elif menu == "Budget":
    budget_ui(supabase)

elif menu == "Budget vs Réel":
    budget_vs_reel_ui(supabase)

elif menu == "Contrôle répartition":
    controle_repartition_ui(supabase)