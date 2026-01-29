import streamlit as st

def appels_fonds_trimestre_ui(supabase, annee):
    st.success(f"Appels de fonds par trimestre – année {annee}")