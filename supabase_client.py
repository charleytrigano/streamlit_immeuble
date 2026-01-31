
import streamlit as st
from supabase import create_client


def get_supabase_client():
    """
    Retourne un client Supabase initialisé avec les secrets Streamlit.
    Utilise UNIQUEMENT la clé anonyme.
    """

    try:
        url = st.secrets["SUPABASE_URL"]
        key = st.secrets["SUPABASE_ANON_KEY"]
    except KeyError:
        st.error(
            "❌ Supabase mal configuré.\n\n"
            "Dans `.streamlit/secrets.toml`, tu dois avoir :\n"
            "SUPABASE_URL = \"...\"\n"
            "SUPABASE_ANON_KEY = \"...\""
        )
        st.stop()

    return create_client(url, key)