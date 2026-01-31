import streamlit as st
from config import get_supabase_client
from appels_fonds_ui import appels_fonds_ui

st.set_page_config(page_title="Gestion Immeuble", layout="wide")

st.title("🏢 Gestion de l’immeuble")

# Init Supabase
supabase = get_supabase_client()
st.success("✅ Supabase connecté")

# Affichage direct de l’onglet (PAS DE MENU POUR L’INSTANT)
appels_fonds_ui(supabase)