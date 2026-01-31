import streamlit as st
from supabase import create_client

st.set_page_config(page_title="Test App", layout="wide")

st.write("✅ app.py chargé")

@st.cache_resource
def get_supabase():
    st.write("🔌 Initialisation Supabase")
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_ANON_KEY"]
    return create_client(url, key)

def main():
    st.title("🧪 Test affichage onglet")

    supabase = get_supabase()
    st.success("✅ Supabase OK")

    st.write("📦 Import du module appels_fonds_ui…")

    try:
        from appels_fonds_ui import appels_fonds_ui
        st.success("✅ Import appels_fonds_ui OK")
    except Exception as e:
        st.error("❌ Échec import appels_fonds_ui")
        st.exception(e)
        st.stop()

    st.write("🚀 Appel de la fonction UI")
    appels_fonds_ui(supabase)

if __name__ == "__main__":
    main()