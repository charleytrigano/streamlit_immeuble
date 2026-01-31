import streamlit as st
from supabase import create_client

# =========================
# CONFIG STREAMLIT
# =========================
st.set_page_config(
    page_title="Pilotage des charges - Dépenses",
    layout="wide"
)

# =========================
# SUPABASE (ANON KEY)
# =========================
@st.cache_resource
def get_supabase():
    """
    Connexion Supabase avec SUPABASE_URL et SUPABASE_ANON_KEY
    définis dans .streamlit/secrets.toml
    """
    try:
        url = st.secrets["SUPABASE_URL"]
        key = st.secrets["SUPABASE_ANON_KEY"]
    except KeyError:
        st.error(
            "❌ Supabase mal configuré.\n\n"
            "Vérifie `.streamlit/secrets.toml` avec les clés :\n"
            "  - SUPABASE_URL\n"
            "  - SUPABASE_ANON_KEY"
        )
        st.stop()

    return create_client(url, key)


def main():
    supabase = get_supabase()

    # =========================
    # FILTRE GLOBAL ANNÉE
    # =========================
    st.sidebar.title("🔎 Filtres globaux")
    annee = st.sidebar.selectbox(
        "Année",
        options=[2023, 2024, 2025, 2026],
        index=2  # 2025 par défaut
    )

    st.title("📊 Pilotage des charges – Dépenses")

    # Import et appel du module Dépenses
    from depenses_ui import depenses_ui
    depenses_ui(supabase, annee)


if __name__ == "__main__":
    main()