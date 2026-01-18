import pandas as pd
import streamlit as st

def plot_charges_par_poste(df):
    data = (
        df.groupby("Poste")["Montant TTC"]
          .sum()
          .sort_values(ascending=False)
    )
    st.subheader("Répartition des charges par poste")
    st.bar_chart(data)

def plot_pareto_postes(df):
    data = (
        df.groupby("Poste")["Montant TTC"]
          .sum()
          .sort_values(ascending=False)
          .reset_index()
    )
    data["Cumul %"] = data["Montant TTC"].cumsum() / data["Montant TTC"].sum() * 100

    st.subheader("Analyse Pareto des charges (80/20)")
    st.dataframe(data)

def plot_top_fournisseurs(df, top_n=10):
    data = (
        df.groupby("Fournisseur")["Montant TTC"]
          .sum()
          .sort_values(ascending=False)
          .head(top_n)
    )
    st.subheader(f"Top {top_n} fournisseurs")
    st.bar_chart(data)

def plot_recurrent_vs_ponctuel(df):
    data = (
        df.groupby("Type")["Montant TTC"]
          .sum()
    )
    st.subheader("Charges récurrentes vs ponctuelles")
    st.bar_chart(data)

