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
# SUPABASE
# =========================
@st.cache_resource
def get_supabase():
    try:
        url = st.secrets["SUPABASE_URL"]
        key = st.secrets["SUPABASE_ANON_KEY"]
    except KeyError:
        st.error(
            "❌ Clés Supabase manquantes.\n\n"
            "Vérifie `.streamlit/secrets.toml` :\n"
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
    st.sidebar.title("🔎 Filtres globaux")

    annee = st.sidebar.selectbox(
        "Année",
        options=[2023, 2024, 2025, 2026],
        index=2
    )

    # =========================
    # TITRE
    # =========================
    st.title("📊 Pilotage des charges de l’immeuble")

    # =========================
    # ONGLET PRINCIPAL
    # =========================
    tab_dep, tab_bud, tab_bvr, tab_plan = st.tabs([
        "📄 Dépenses",
        "💰 Budget",
        "📊 Budget vs Réel",
        "📘 Plan comptable"
    ])

    # =========================
    # DÉPENSES
    # =========================
    with tab_dep:
        try:
            from depenses_ui import depenses_ui
            depenses_ui(supabase, annee)
        except Exception as e:
            st.error("❌ Erreur dans Dépenses")
            st.exception(e)

    # =========================
    # BUDGET
    # =========================
    with tab_bud:
        try:
            from budget_ui import budget_ui
            budget_ui(supabase, annee)
        except Exception as e:
            st.error("❌ Erreur dans Budget")
            st.exception(e)

    # =========================
    # BUDGET VS RÉEL
    # =========================
    with tab_bvr:
        try:
            from budget_vs_reel_ui import budget_vs_reel_ui
            budget_vs_reel_ui(supabase, annee)
        except Exception as e:
            st.error("❌ Erreur dans Budget vs Réel")
            st.exception(e)

    # =========================
    # PLAN COMPTABLE
    # =========================
    with tab_plan:
        try:
            from plan_comptable_ui import plan_comptable_ui
            plan_comptable_ui(supabase)
        except Exception as e:
            st.error("❌ Erreur dans Plan comptable")
            st.exception(e)


# =========================
# RUN
# =========================
if __name__ == "__main__":
    main()