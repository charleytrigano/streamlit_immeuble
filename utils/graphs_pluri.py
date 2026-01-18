import streamlit as st

def plot_trend_par_poste(df, poste):
    data = df[df["Poste"] == poste].set_index("Année")["Montant_Total"]

    st.subheader(f"Évolution pluriannuelle – {poste}")
    st.line_chart(data)


def plot_global_trends(df):
    data = (
        df.groupby("Année")["Montant_Total"]
        .sum()
        .reset_index()
        .set_index("Année")
    )

    st.subheader("Évolution globale des charges")
    st.line_chart(data)

