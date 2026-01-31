import streamlit as st
import pandas as pd

def budget_vs_reel_ui(supabase, annee):
    st.subheader(f"📊 Budget vs Réel – {annee}")

    st.info("Module chargé correctement ✅")

    # test simple
    st.write("Supabase OK :", supabase is not None)
    st.write("Année :", annee)