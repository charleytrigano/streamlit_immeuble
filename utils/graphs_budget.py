import streamlit as st

def plot_budget_vs_reel(df):
    st.subheader("Budget voté vs Dépenses réelles")

    chart_data = df.set_index("Poste")[["Budget", "Réel"]]
    st.bar_chart(chart_data)
