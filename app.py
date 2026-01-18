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
# OUTILS
# =========================
def normalize_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Normalise systématiquement les noms de colonnes"""
    return df.rename(columns={
        "Année": "annee",
        "Compte": "compte",
        "Montant TTC": "montant_ttc",
        "Montant": "montant_ttc",
        "Budget": "budget"
    })

# =========================
# IMPORT DEPENSES
# =========================
st.markdown("## 📥 Import des dépenses")

uploaded_csv = st.file_uploader("Base des dépenses (CSV)", type=["csv"])

if uploaded_csv:
    df = pd.read_csv(uploaded_csv, sep=None, engine="python")
    df.columns = [c.strip().replace("\ufeff", "") for c in df.columns]
    df = normalize_columns(df)

    required = ["annee", "compte", "montant_ttc"]
    missing = [c for c in required if c not in df.columns]

    if missing:
        st.error(f"Colonnes manquantes : {', '.join(missing)}")
    else:
        df["compte"] = df["compte"].astype(str)
        st.session_state.df_factures = df
        st.success("Dépenses chargées")

# =========================
# STOP
# =========================
if st.session_state.df_factures is None:
    st.stop()

df = st.session_state.df_factures.copy()

# =========================
# FILTRE ANNÉE
# =========================
annees = sorted(df["annee"].dropna().unique())
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
    df_budget = normalize_columns(df_budget)

    required = ["annee", "compte", "budget"]
    missing = [c for c in required if c not in df_budget.columns]

    if missing:
        st.error(f"Colonnes budget manquantes : {', '.join(missing)}")
    else:
        df_budget["compte"] = df_budget["compte"].astype(str)
        st.session_state.df_budget = df_budget
        st.success("Budget chargé")

df_budget = st.session_state.df_budget.copy()

# =========================
# 📊 BUDGET vs RÉEL (CORRIGÉ)
# =========================
if not df_budget.empty:
    st.markdown("## 📊 Budget vs Réel")

    budget_annee = df_budget[df_budget["annee"] == annee_sel].copy()
    budget_annee["compte"] = budget_annee["compte"].astype(str)

    # clés budgétaires = SOURCE DE VÉRITÉ
    cles_budget = sorted(
        budget_annee["compte"].unique(),
        key=len,
        reverse=True
    )

    def map_budget(compte_reel: str):
        for cle in cles_budget:
            if compte_reel.startswith(cle):
                return cle
        return "NON BUDGÉTÉ"

    df_annee["cle_budget"] = df_annee["compte"].apply(map_budget)

    reel = (
        df_annee.groupby("cle_budget")["montant_ttc"]
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

    comp["budget"] = comp["budget"].fillna(0)
    comp["ecart_eur"] = comp["reel"] - comp["budget"]
    comp["ecart_pct"] = comp.apply(
        lambda r: (r["ecart_eur"] / r["budget"] * 100)
        if r["budget"] != 0 else None,
        axis=1
    )

    st.dataframe(
        comp[["cle_budget", "reel", "budget", "ecart_eur", "ecart_pct"]],
        use_container_width=True
    )

# =========================
# FOOTER
# =========================
st.markdown("---")
st.markdown("*Application de pilotage – Conseil syndical / Copropriété*")
