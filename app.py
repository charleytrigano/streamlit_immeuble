import streamlit as st
import pandas as pd

# =========================
# CONFIG STREAMLIT
# =========================
st.set_page_config(page_title="Pilotage des charges", layout="wide")

st.title("Pilotage des charges de l’immeuble")
st.markdown(
    "Budget suivi à **granularité variable** (3 ou 4 chiffres selon le budget)."
)

# =========================
# SESSION STATE
# =========================
if "df_factures" not in st.session_state:
    st.session_state.df_factures = None

if "df_budget" not in st.session_state:
    st.session_state.df_budget = pd.DataFrame(
        columns=["annee", "compte", "budget"]
    )

# =========================
# IMPORT DEPENSES
# =========================
st.markdown("## 📥 Import des dépenses")

uploaded_csv = st.file_uploader("Base des dépenses (CSV)", type=["csv"])

if uploaded_csv:
    df = pd.read_csv(uploaded_csv, sep=None, engine="python")
    df.columns = [c.strip().replace("\ufeff", "") for c in df.columns]

    df = df.rename(columns={
        "Année": "annee",
        "Montant TTC": "montant_ttc"
    })

    df["Compte"] = df["Compte"].astype(str)

    st.session_state.df_factures = df
    st.success("Dépenses chargées")

# =========================
# STOP
# =========================
if st.session_state.df_factures is None:
    st.stop()

df = st.session_state.df_factures

annees = sorted(df["annee"].unique())
annee_sel = st.selectbox("Exercice", annees)

df_annee = df[df["annee"] == annee_sel].copy()

# =========================
# IMPORT BUDGET
# =========================
st.markdown("## 💰 Import du budget")

uploaded_budget = st.file_uploader("Budget (CSV)", type=["csv"], key="budget")

if uploaded_budget:
    df_budget = pd.read_csv(uploaded_budget, sep=None, engine="python")
    df_budget.columns = [c.strip().replace("\ufeff", "") for c in df_budget.columns]

    df_budget = df_budget.rename(columns={
        "Année": "annee",
        "Compte": "compte",
        "Budget": "budget"
    })

    df_budget["compte"] = df_budget["compte"].astype(str)

    st.session_state.df_budget = df_budget
    st.success("Budget chargé")

df_budget = st.session_state.df_budget

# =========================
# BUDGET VS REEL (ROBUSTE)
# =========================
if not df_budget.empty:
    st.markdown("## 📊 Budget vs Réel")

    budget_annee = df_budget[df_budget["annee"] == annee_sel].copy()

    # Liste des clés budgétaires triées par longueur décroissante
    cles_budget = sorted(
        budget_annee["compte"].unique(),
        key=len,
        reverse=True
    )

    def map_cle(compte):
        for cle in cles_budget:
            if compte.startswith(cle):
                return cle
        return None

    df_annee["cle_budget"] = df_annee["Compte"].apply(map_cle)

    reel = (
        df_annee.groupby("cle_budget", dropna=False)["montant_ttc"]
        .sum()
        .reset_index()
        .rename(columns={"montant_ttc": "reel"})
    )

    comp = reel.merge(
        budget_annee,
        left_on="cle_budget",
        right_on="compte",
        how="left"
    )

    comp["ecart_eur"] = comp["reel"] - comp["budget"]
    comp["ecart_pct"] = (comp["ecart_eur"] / comp["budget"]) * 100

    # Colonnes garanties
    comp_aff = comp[
        ["cle_budget", "reel", "budget", "ecart_eur", "ecart_pct"]
    ]

    st.dataframe(comp_aff, use_container_width=True)

# =========================
# FOOTER
# =========================
st.markdown("---")
st.markdown("*Application de pilotage – Conseil syndical / Copropriété*")
