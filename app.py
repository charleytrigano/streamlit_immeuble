import streamlit as st
from supabase_client import get_supabase

# -----------------------------
# Configuration page
# -----------------------------
st.set_page_config(
    page_title="Pilotage des charges",
    layout="wide"
)

# -----------------------------
# Connexion Supabase
# -----------------------------
supabase = get_supabase()
st.success("✅ Supabase connecté correctement")

# -----------------------------
# Filtres globaux
# -----------------------------
st.sidebar.title("🔎 Filtres globaux")

annee = st.sidebar.selectbox(
    "Année",
    [2023, 2024, 2025],
    index=2,
    key="filtre_annee"
)

# -----------------------------
# Navigation principale
# -----------------------------
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

# -----------------------------
# Pages
# -----------------------------
def safe_import(module_name, func_name):
    try:
        module = __import__(module_name, fromlist=[func_name])
        return getattr(module, func_name)
    except Exception as e:
        st.error(f"❌ Impossible de charger {module_name}.{func_name}")
        st.exception(e)
        return None


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