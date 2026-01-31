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

    # =========================
    # SIDEBAR – FILTRES
    # =========================
    st.sidebar.title("🔎 Filtres globaux")

    annee = st.sidebar.selectbox(
        "Année",
        [2023, 2024, 2025, 2026],
        index=2
    )

    # =========================
    # TITRE
    # =========================
    st.title("📊 Pilotage des charges de l’immeuble")

    # =========================
    # ONGLET DÉPENSES
    # =========================
    from depenses_ui import depenses_ui
    depenses_ui(supabase, annee)

# =========================
# RUN
# =========================
if __name__ == "__main__":
    main()