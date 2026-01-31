import streamlit as st
from utils.supabase_client import get_supabase_client

st.set_page_config(page_title="Immeuble pilotage", layout="wide")

st.title("Test Supabase")

supabase = get_supabase_client()

st.success("Connexion Supabase OK 🎉")