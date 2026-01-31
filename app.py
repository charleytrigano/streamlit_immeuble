import streamlit as st
from supabase import create_client

@st.cache_resource
def get_supabase():
    try:
        url = st.secrets["SUPABASE_URL"]
        key = st.secrets["SUPABASE_ANON_KEY"]
    except KeyError as e:
        st.error("❌ Clé manquante dans st.secrets")
        st.code(str(e))
        st.stop()

    return create_client(url, key)

supabase = get_supabase()

st.success("✅ Supabase connecté correctement")