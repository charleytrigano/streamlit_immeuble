import streamlit as st

def plot_projection(df):
    st.subheader("Projection des charges")

    chart = (
        df.groupby(["Année", "Scénario"])["Montant_Projeté"]
        .sum()
        .reset_index()
        .pivot(index="Année", columns="Scénario", values="Montant_Projeté")
    )

    st.line_chart(chart)

