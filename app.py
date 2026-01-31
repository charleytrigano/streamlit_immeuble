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
    try:
        url = st.secrets["SUPABASE_URL"]
        key = st.secrets["SUPABASE_ANON_KEY"]
    except KeyError:
        st.error(
            "❌ Supabase mal configuré\n\n"
            "Clés requises :\n"
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
    # FILTRES GLOBAUX
    # =========================
    st.sidebar.title("🔎 Filtres globaux")

    annee = st.sidebar.selectbox(
        "Année",
        [2023, 2024, 2025, 2026],
        index=2
    )

    st.title("📊 Pilotage des charges de l’immeuble")

    # =========================
    # ONGLET PRINCIPAL
    # =========================
    (
        tab_dep,
        tab_bud,
        tab_bvr,
        tab_appels,
        tab_repart,
        tab_plan,
        tab_lots
    ) = st.tabs([
        "📄 Dépenses",
        "💰 Budget",
        "📊 Budget vs Réel",
        "📢 Appels de fonds trimestriels",
        "🏢 Répartition par lot",
        "📘 Plan comptable",
        "🏠 Lots"
    ])

    # =========================
    # DÉPENSES
    # =========================
    with tab_dep:
        from utils.depenses_ui import depenses_ui
        depenses_ui(supabase, annee)

    # =========================
    # BUDGET
    # =========================
    with tab_bud:
        from utils.budget_ui import budget_ui
        budget_ui(supabase, annee)

    # =========================
    # BUDGET VS RÉEL
    # =========================
    with tab_bvr:
        from utils.budget_vs_reel_ui import budget_vs_reel_ui
        budget_vs_reel_ui(supabase, annee)

    # =========================
    # APPELS DE FONDS TRIMESTRIELS ✅
    # =========================
    with tab_appels:
        from utils.appels_fonds_trimestre_ui import appels_fonds_trimestre_ui
        appels_fonds_trimestre_ui(supabase, annee)

    # =========================
    # RÉPARTITION PAR LOT
    # =========================
    with tab_repart:
        from utils.repartition_lots_ui import repartition_lots_ui
        repartition_lots_ui(supabase, annee)

    # =========================
    # PLAN COMPTABLE
    # =========================
    with tab_plan:
        from utils.plan_comptable_ui import plan_comptable_ui
        plan_comptable_ui(supabase)

    # =========================
    # LOTS
    # =========================
    with tab_lots:
        from utils.lots_ui import lots_ui
        lots_ui(supabase)

# =========================
# RUN
# =========================
if __name__ == "__main__":
    main()