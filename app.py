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
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_ANON_KEY"]
    return create_client(url, key)

# =========================
# MAIN
# =========================
def main():
    supabase = get_supabase()

    st.sidebar.title("🔎 Filtres globaux")
    annee = st.sidebar.selectbox("Année", [2023, 2024, 2025, 2026], index=2)

    st.title("📊 Pilotage des charges de l’immeuble")

    tab_dep, tab_bud, tab_bvr, tab_plan = st.tabs([
        "📄 Dépenses",
        "💰 Budget",
        "📊 Budget vs Réel",
        "📘 Plan comptable"
    ])

    with tab_dep:
        from depenses_ui import depenses_ui
        depenses_ui(supabase, annee)

    with tab_bud:
        from budget_ui import budget_ui
        budget_ui(supabase, annee)

    with tab_bvr:
        from budget_vs_reel_ui import budget_vs_reel_ui
        budget_vs_reel_ui(supabase, annee)

    with tab_plan:
        from plan_comptable_ui import plan_comptable_ui
        plan_comptable_ui(supabase)

if __name__ == "__main__":
    main()