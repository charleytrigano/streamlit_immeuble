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
# SUPABASE (ANON KEY)
# =========================
@st.cache_resource
def get_supabase():
    """
    Connexion Supabase avec les secrets Streamlit :
    - SUPABASE_URL
    - SUPABASE_ANON_KEY
    """
    try:
        url = st.secrets["SUPABASE_URL"]
        key = st.secrets["SUPABASE_ANON_KEY"]
    except KeyError:
        st.error(
            "❌ Supabase mal configuré.\n\n"
            "Vérifie `.streamlit/secrets.toml` :\n"
            "SUPABASE_URL\n"
            "SUPABASE_ANON_KEY"
        )
        st.stop()

    return create_client(url, key)


# =========================
# IMPORT DES MODULES UI
# (tous les fichiers .py doivent être à côté de app.py)
# =========================
from depenses_ui import depenses_ui
from budget_ui import budget_ui
from budget_vs_reel_ui import budget_vs_reel_ui
from appels_fonds_trimestre_ui import appels_fonds_trimestre_ui
from repartition_lots_ui import repartition_lots_ui
from plan_comptable_ui import plan_comptable_ui
from lots_ui import lots_ui


# =========================
# MAIN
# =========================
def main():
    supabase = get_supabase()

    # =========================
    # SIDEBAR – FILTRES
    # =========================
    st.sidebar.title("🔎 Filtres globaux")

    annee = st.sidebar.selectbox(
        "Année",
        options=[2023, 2024, 2025, 2026],
        index=2  # 2025 par défaut
    )

    # =========================
    # TITRE
    # =========================
    st.title("📊 Pilotage des charges de l’immeuble")

    # =========================
    # ONGLET PRINCIPAL
    # =========================
    tab_dep, tab_bud, tab_bvr, tab_appels, tab_repart, tab_plan, tab_lots = st.tabs([
        "📄 Dépenses",
        "💰 Budget",
        "📊 Budget vs Réel",
        "📢 Appels de fonds trimestriels",
        "🏢 Répartition par lot",
        "📘 Plan comptable",
        "🏠 Lots",
    ])

    # =========================
    # 📄 DÉPENSES
    # =========================
    with tab_dep:
        try:
            depenses_ui(supabase, annee)
        except Exception as e:
            st.error("❌ Erreur module Dépenses")
            st.exception(e)

    # =========================
    # 💰 BUDGET
    # =========================
    with tab_bud:
        try:
            budget_ui(supabase, annee)
        except Exception as e:
            st.error("❌ Erreur module Budget")
            st.exception(e)

    # =========================
    # 📊 BUDGET VS RÉEL
    # =========================
    with tab_bvr:
        try:
            budget_vs_reel_ui(supabase, annee)
        except Exception as e:
            st.error("❌ Erreur module Budget vs Réel")
            st.exception(e)

    # =========================
    # 📢 APPELS DE FONDS TRIMESTRIELS
    # =========================
    with tab_appels:
        try:
            appels_fonds_trimestre_ui(supabase, annee)
        except Exception as e:
            st.error("❌ Erreur module Appels de fonds trimestriels")
            st.exception(e)

    # =========================
    # 🏢 RÉPARTITION PAR LOT
    # =========================
    with tab_repart:
        try:
            repartition_lots_ui(supabase, annee)
        except Exception as e:
            st.error("❌ Erreur module Répartition par lot")
            st.exception(e)

    # =========================
    # 📘 PLAN COMPTABLE
    # =========================
    with tab_plan:
        try:
            plan_comptable_ui(supabase)
        except Exception as e:
            st.error("❌ Erreur module Plan comptable")
            st.exception(e)

    # =========================
    # 🏠 LOTS
    # =========================
    with tab_lots:
        try:
            lots_ui(supabase)
        except Exception as e:
            st.error("❌ Erreur module Lots")
            st.exception(e)


# =========================
# RUN
# =========================
if __name__ == "__main__":
    main()