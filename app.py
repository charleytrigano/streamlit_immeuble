import streamlit as st
from supabase import create_client

st.set_page_config(page_title="Test Supabase", layout="wide")

st.title("🔍 Test configuration Supabase")

st.subheader("Contenu de st.secrets :")
st.write(st.secrets)

try:
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_ANON_KEY"]
    st.success("✅ Clés trouvées dans st.secrets")
except KeyError as e:
    st.error("❌ Clé manquante dans st.secrets")
    st.code(str(e))
    st.stop()

supabase = create_client(url, key)

st.success("🚀 Connexion Supabase OK")