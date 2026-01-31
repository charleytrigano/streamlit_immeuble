import streamlit as st
from supabase import create_client

# ======================================================
# CONFIG STREAMLIT
# ======================================================
st.set_page_config(
    page_title="Pilotage des charges",
    layout="wide"
)

# ======================================================
# SUPABASE (ANON KEY UNIQUEMENT)
# ======================================================
@st.cache_resource
def get_supabase():
    try:
        url = st.secrets["SUPABASE_URL"]
        key = st.secrets["SUPABASE_ANON_KEY"]
    except KeyError:
        st.error(
            "❌ Clés Supabase manquantes dans st.secrets\n\n"
            "Attendu :\n"
            "- SUPABASE_URL\n"
            "- SUPABASE_ANON_KEY"
        )
        st.stop()

    return create_client(url, key)

# ======================================================
# MAIN
# ======================================================
def main():
    supabase = get_supabase()

    # ------------------------------
    # SIDEBAR – FILTRES GLOBAUX
    # ------------------------------
    st.sidebar.title("🔎 Filtres globaux")

    annee = st.sidebar.selectbox(
        "Année",
        [2023, 2024, 2025, 2026],
        index=2
    )

    # ------------------------------
    # TITRE
    # ------------------------------
    st.title("📊 Pilotage des charges de l’immeuble")

    # ------------------------------
    # ONGLET PRINCIPAL
    # ------------------------------
    tab_depenses, = st.tabs([
        "📄 Dépenses"
    ])

    # ------------------------------
    # DÉPENSES
    # ------------------------------
    with tab_depenses:
        try:
            from depenses_ui import depenses_ui
            depenses_ui(supabase, annee)
        except Exception as e:
            st.error("❌ Erreur dans le module Dépenses")
            st.exception(e)


# ======================================================
# RUN
# ======================================================
if __name__ == "__main__":
    main()