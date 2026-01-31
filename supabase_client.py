import streamlit as st
from supabase import create_client


def get_supabase_client():
    try:
        url = st.secrets["SUPABASE_URL"]
        key = st.secrets["SUPABASE_ANON_KEY"]
    except KeyError:
        st.error(
            "❌ Supabase mal configuré.\n\n"
            "Ajoute dans secrets.toml :\n"
            "SUPABASE_URL\n"
            "SUPABASE_ANON_KEY"
        )
        st.stop()

    return create_client(url, key)