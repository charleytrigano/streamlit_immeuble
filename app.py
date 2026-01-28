import streamlit as st
from supabase import create_client

# =====================================================
# CONFIG STREAMLIT
# =====================================================
st.set_page_config(
    page_title="Pilotage des charges",
    layout="wide"
)

# =====================================================
# SUPABASE (ANON KEY UNIQUEMENT)
# =====================================================
@st.cache_resource
def get_supabase():
    try:
        url = st.secrets["SUPABASE_URL"]
        key = st.secrets["SUPABASE_ANON_KEY"]
    except KeyError:
        st.error(
            "❌ Supabase mal configuré.\n\n"
            "Le fichier `.streamlit/secrets.toml` doit contenir :\n\n"
            "SUPABASE_URL\n"
            "SUPABASE_ANON_KEY"
        )
        st.stop()

    return create_client(url, key)

# =====================================================
# MAIN
# =====================================================
def main():
    supabase = get_supabase()

    # =================================================
    # SIDEBAR — FILTRES GLOBAUX
    # =================================================
    st.sidebar.title("🔎 Filtres globaux")

    annee = st.sidebar.selectbox(
        "Année",
        options=[2023, 2024, 2025, 2026],
        index=2
    )

    # =================================================
    # TITRE
    # =================================================
    st.title("📊 Pilotage des charges de l’immeuble")

    # =================================================
    # ONGLET PRINCIPAL
    # =================================================
    tab_dep, tab_bud, tab_bvr, tab_rep, tab_plan, tab_lots = st.tabs([
        "📄 Dépenses",
        "💰 Budget",
        "📊 Budget vs Réel",
        "🏢 Répartition par lot",
        "📘 Plan comptable",
        "🏠 Lots"
    ])

    # =================================================
    # DÉPENSES
    # =================================================
    with tab_dep:
        try:
            from utils.depenses_ui import depenses_ui
            depenses_ui(supabase, annee)
        except Exception as e:
            st.error("❌ Erreur dans le module Dépenses")
            st.exception(e)

    # =================================================
    # BUDGET
    # =================================================
    with tab_bud:
        try:
            from utils.budget_ui import budget_ui
            budget_ui(supabase, annee)
        except Exception as e:
            st.error("❌ Erreur dans le module Budget")
            st.exception(e)

    # =================================================
    # BUDGET VS RÉEL
    # =================================================
    with tab_bvr:
        try:
            from utils.budget_vs_reel_ui import budget_vs_reel_ui
            budget_vs_reel_ui(supabase, annee)
        except Exception as e:
            st.error("❌ Erreur dans le module Budget vs Réel")
            st.exception(e)

    # =================================================
    # RÉPARTITION PAR LOT
    # =================================================
    with tab_rep:
        try:
            from utils.repartition_lots_ui import repartition_lots_ui
            repartition_lots_ui(supabase, annee)
        except Exception as e:
            st.error("❌ Erreur dans le module Répartition par lot")
            st.exception(e)

    # =================================================
    # PLAN COMPTABLE
    # =================================================
    with tab_plan:
        try:
            from utils.plan_comptable_ui import plan_comptable_ui
            plan_comptable_ui(supabase)
        except Exception as e:
            st.error("❌ Erreur dans le module Plan comptable")
            st.exception(e)

    # =================================================
    # LOTS
    # =================================================
    with tab_lots:
        try:
            from utils.lots_ui import lots_ui
            lots_ui(supabase)
        except Exception as e:
            st.error("❌ Erreur dans le module Lots")
            st.exception(e)


# =====================================================
# RUN
# =====================================================
if __name__ == "__main__":
    main()