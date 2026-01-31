import streamlit as st
from supabase import create_client, Client


def get_supabase() -> Client:
    """
    Initialise et retourne le client Supabase.
    Les clés doivent être définies dans .streamlit/secrets.toml
    """
    try:
        url = st.secrets["supabase_url"]
        key = st.secrets["supabase_anon_key"]
    except KeyError as e:
        st.error(f"❌ Clé Supabase manquante dans st.secrets : {e}")
        st.stop()

    return create_client(url, key)