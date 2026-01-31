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
            "❌ Supabase mal configuré.\n\n"
            "Vérifie `.streamlit/secrets.toml` avec :\n"
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

    st.title("📊 Pilotage des charges de l’immeuble")

    # ===== ONGLET UNIQUE POUR TEST =====
    tab = st.tabs(["📢 Appels de fonds trimestriels"])[0]

    with tab:
        from appels_fonds_ui import appels_fonds_ui
        appels_fonds_ui(supabase)

# =========================
# RUN
# =========================
if __name__ == "__main__":
    main()