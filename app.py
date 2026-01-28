import streamlit as st
from supabase import create_client

# =========================
# CONFIG STREAMLIT
# =========================
st.set_page_config(
    page_title="Pilotage des charges",
    layout="wide"
)

# =========================
# SUPABASE (ANON KEY ONLY)
# =========================
@st.cache_resource
def get_supabase():
    try:
        url = st.secrets["SUPABASE_URL"]
        key = st.secrets["SUPABASE_ANON_KEY"]
    except KeyError:
        st.error(
            "❌ Supabase mal configuré.\n\n"
            "Vérifie `.streamlit/secrets.toml` :\n\n"
            "SUPABASE_URL\n"
            "SUPABASE_ANON_KEY"
        )
        st.stop()

    return create_client(url, key)

# =========================
# MAIN
# =========================
def main():
    supabase = get_supabase()

    # =========================
    # SIDEBAR – FILTRES GLOBAUX
    # =========================
    st.sidebar.title("🔎 Filtres")

    annee = st.sidebar.selectbox(
        "Année",
        options=[2023, 2024, 2025, 2026],
        index=2
    )

    # =========================
    # ONGLET PRINCIPAL
    # =========================
    st.title("📊 Pilotage des charges de l’immeuble")

    tab_dep, tab_bud, tab_plan, tab_lots = st.tabs([
        "📄 Dépenses",
        "💰 Budget",
        "📘 Plan comptable",
        "🏢 Lots"
    ])

    # =========================
    # DÉPENSES
    # =========================
    with tab_dep:
        try:
            from utils.depenses_ui import depenses_ui
            depenses_ui(supabase, annee)
        except Exception as e:
            st.error("Erreur module Dépenses")
            st.exception(e)

    # =========================
    # BUDGET
    # =========================
    with tab_bud:
        try:
            from utils.budget_ui import budget_ui
            budget_ui(supabase, annee)
        except Exception as e:
            st.error("Erreur module Budget")
            st.exception(e)

    # =========================
    # PLAN COMPTABLE
    # =========================
    with tab_plan:
        try:
            from utils.plan_comptable_ui import plan_comptable_ui
            plan_comptable_ui(supabase)
        except Exception as e:
            st.error("Erreur module Plan comptable")
            st.exception(e)

    # =========================
    # LOTS
    # =========================
    with tab_lots:
        try:
            from utils.lots_ui import lots_ui
            lots_ui(supabase)
        except Exception as e:
            st.error("Erreur module Lots")
            st.exception(e)

# =========================
# RUN
# =========================
if __name__ == "__main__":
    main()