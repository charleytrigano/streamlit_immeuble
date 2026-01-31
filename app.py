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
# SUPABASE — INITIALISATION DIRECTE (SANS IMPORT LOCAL)
# =========================================================
def get_supabase() -> Client:
    try:
        url = st.secrets["supabase_url"]
        key = st.secrets["supabase_anon_key"]
    except KeyError as e:
        st.error(f"❌ Clé Supabase manquante dans st.secrets : {e}")
        st.stop()

    return create_client(url, key)


supabase = get_supabase()
st.success("✅ Supabase connecté correctement")

# =========================================================
# FILTRES GLOBAUX
# =========================================================
st.sidebar.title("🔎 Filtres globaux")

annee = st.sidebar.selectbox(
    "Année",
    [2023, 2024, 2025],
    index=2,
    key="filtre_annee"
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
# CHARGEMENT SÉCURISÉ DES MODULES UI
# =========================================================
def safe_import(module_name, func_name):
    try:
        module = __import__(module_name, fromlist=[func_name])
        return getattr(module, func_name)
    except Exception as e:
        st.error(f"❌ Impossible de charger {module_name}.{func_name}")
        st.exception(e)
        return None


# =========================================================
# ROUTAGE DES PAGES
# =========================================================
if page == "📄 Dépenses":
    ui = safe_import("depenses_ui", "depenses_ui")
    if ui:
        ui(supabase, annee)

elif page == "💰 Budget":
    ui = safe_import("budget_ui", "budget_ui")
    if ui:
        ui(supabase, annee)

elif page == "📊 Budget vs Réel":
    ui = safe_import("budget_vs_reel_ui", "budget_vs_reel_ui")
    if ui:
        ui(supabase, annee)

elif page == "📘 Plan comptable":
    ui = safe_import("plan_comptable_ui", "plan_comptable_ui")
    if ui:
        ui(supabase)