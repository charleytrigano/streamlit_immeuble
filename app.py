import streamlit as st
from supabase import create_client, Client

# =========================================================
# CONFIG STREAMLIT
# =========================================================
st.set_page_config(
    page_title="Pilotage des charges",
    layout="wide"
)

# =========================================================
# SUPABASE — CONNEXION DIRECTE
# =========================================================
def get_supabase() -> Client:
    try:
        url = st.secrets["supabase_url"]
        key = st.secrets["supabase_anon_key"]
    except KeyError as e:
        st.error(f"❌ Clé Supabase manquante : {e}")
        st.stop()

    return create_client(url, key)

supabase = get_supabase()

# =========================================================
# FILTRES GLOBAUX
# =========================================================
st.sidebar.title("🔎 Filtres globaux")

annee = st.sidebar.selectbox(
    "Année",
    [2023, 2024, 2025],
    index=2,
    key="filtre_annee_global"
)

# =========================================================
# NAVIGATION
# =========================================================
st.sidebar.title("📊 Pilotage des charges")

page = st.sidebar.radio(
    "Navigation",
    [
        "📄 Dépenses",
        "💰 Budget",
        "📊 Budget vs Réel",
        "📘 Plan comptable",
    ],
    key="navigation_principale"
)

# =========================================================
# ROUTAGE
# =========================================================
if page == "📄 Dépenses":
    from depenses_ui import depenses_ui
    depenses_ui(supabase, annee)

elif page == "💰 Budget":
    from budget_ui import budget_ui
    budget_ui(supabase, annee)

elif page == "📊 Budget vs Réel":
    from budget_vs_reel_ui import budget_vs_reel_ui
    budget_vs_reel_ui(supabase, annee)

elif page == "📘 Plan comptable":
    from plan_comptable_ui import plan_comptable_ui
    plan_comptable_ui(supabase)