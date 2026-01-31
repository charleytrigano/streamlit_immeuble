import streamlit as st

from supabase_client import get_supabase_client

from depenses_ui import depenses_ui
from depenses_detail_ui import depenses_detail_ui


# ======================================================
# Configuration Streamlit
# ======================================================
st.set_page_config(
    page_title="Pilotage des charges",
    layout="wide",
)


# ======================================================
# Sidebar – Filtres globaux
# ======================================================
st.sidebar.title("🔎 Filtres globaux")

annee = st.sidebar.selectbox(
    "Année",
    [2023, 2024, 2025],
    index=2
)


# ======================================================
# Supabase
# ======================================================
supabase = get_supabase_client()


# ======================================================
# App principale
# ======================================================
def main():
    st.title("📊 Pilotage des charges – Dépenses")

    tabs = st.tabs([
        "📊 Dépenses par groupe de charges",
        "📄 Détail des dépenses",
    ])

    # ----------------------------
    # Onglet 1 – Synthèse
    # ----------------------------
    with tabs[0]:
        depenses_ui(supabase, annee)

    # ----------------------------
    # Onglet 2 – Détail
    # ----------------------------
    with tabs[1]:
        depenses_detail_ui(supabase, annee)


# ======================================================
# Entrée
# ======================================================
if __name__ == "__main__":
    main()