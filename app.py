import streamlit as st
import pandas as pd

# ======================================================
# CONFIG
# ======================================================
st.set_page_config(page_title="Pilotage des charges", layout="wide")
st.title("Pilotage des charges de l’immeuble")

# ======================================================
# OUTILS
# ======================================================
def normalize_columns(df):
    return df.rename(columns={
        "Année": "annee",
        "Compte": "compte",
        "Montant TTC": "montant_ttc",
        "Budget": "budget",
        "Fournisseur": "fournisseur",
    })

def normalize_budget_account(compte: str) -> str:
    compte = str(compte)
    if compte.startswith(("621", "622")):
        return compte[:4]
    return compte[:3]

# ======================================================
# SESSION STATE
# ======================================================
if "df_depenses" not in st.session_state:
    st.session_state.df_depenses = None

if "df_budget" not in st.session_state:
    st.session_state.df_budget = pd.DataFrame(
        columns=["annee", "compte", "budget"]
    )

# ======================================================
# SIDEBAR — CHARGEMENT
# ======================================================
with st.sidebar:
    st.markdown("## 📂 Chargement des données")

    dep_csv = st.file_uploader("Dépenses (CSV)", type="csv")
    bud_csv = st.file_uploader("Budget (CSV)", type="csv")

    if dep_csv:
        df = pd.read_csv(dep_csv, sep=None, engine="python")
        df.columns = [c.strip().replace("\ufeff", "") for c in df.columns]
        df = normalize_columns(df)
        df["annee"] = df["annee"].astype(int)
        df["compte"] = df["compte"].astype(str)
        st.session_state.df_depenses = df
        st.success("Dépenses chargées")

    if bud_csv:
        dfb = pd.read_csv(bud_csv, sep=None, engine="python")
        dfb.columns = [c.strip().replace("\ufeff", "") for c in dfb.columns]
        dfb = normalize_columns(dfb)
        dfb["annee"] = dfb["annee"].astype(int)
        dfb["compte"] = dfb["compte"].astype(str)
        dfb["compte"] = dfb["compte"].apply(normalize_budget_account)
        st.session_state.df_budget = dfb[["annee", "compte", "budget"]]
        st.success("Budget chargé")

# ======================================================
# STOP SI PAS DE DÉPENSES
# ======================================================
if st.session_state.df_depenses is None:
    st.stop()

df_dep = st.session_state.df_depenses
df_budget = st.session_state.df_budget

# ======================================================
# NAVIGATION
# ======================================================
with st.sidebar:
    page = st.radio(
        "Vue",
        ["📊 État des dépenses", "📊 Budget vs Réel – Analyse"]
    )

# ======================================================
# 📊 ONGLET — BUDGET VS RÉEL AVEC ANALYSE
# ======================================================
if page == "📊 Budget vs Réel – Analyse":

    annee = st.selectbox("Année analysée", sorted(df_dep["annee"].unique()))

    dep = df_dep[df_dep["annee"] == annee].copy()
    bud = df_budget[df_budget["annee"] == annee].copy()

    if bud.empty:
        st.warning("Aucun budget pour cette année.")
        st.stop()

    # Clés budgétaires
    cles_budget = sorted(bud["compte"].unique(), key=len, reverse=True)

    def map_budget(compte_reel):
        for cle in cles_budget:
            if compte_reel.startswith(cle):
                return cle
        return "NON BUDGÉTÉ"

    dep["compte_budget"] = dep["compte"].apply(map_budget)

    # ===== Vue macro Budget vs Réel
    reel_macro = (
        dep.groupby("compte_budget")["montant_ttc"]
        .sum()
        .reset_index(name="reel")
    )

    macro = bud.merge(
        reel_macro,
        left_on="compte",
        right_on="compte_budget",
        how="left"
    )

    macro["reel"] = macro["reel"].fillna(0)
    macro["ecart_eur"] = macro["reel"] - macro["budget"]
    macro["ecart_pct"] = macro["ecart_eur"] / macro["budget"] * 100

    st.markdown("## 📌 Synthèse Budget vs Réel")
    st.dataframe(
        macro[["compte", "budget", "reel", "ecart_eur", "ecart_pct"]],
        use_container_width=True
    )

    # ===== Sélection du compte à analyser
    st.markdown("## 🔍 Analyse détaillée d’un compte budgété")

    compte_sel = st.selectbox(
        "Compte budgétaire",
        macro["compte"].tolist()
    )

    ligne = macro[macro["compte"] == compte_sel].iloc[0]

    col1, col2, col3 = st.columns(3)
    col1.metric("Budget (€)", f"{ligne['budget']:,.2f}".replace(",", " "))
    col2.metric("Réel (€)", f"{ligne['reel']:,.2f}".replace(",", " "))
    col3.metric(
        "Écart (%)",
        f"{ligne['ecart_pct']:.1f} %"
    )

    # ===== Détail par comptes réels
    st.markdown("### 📂 Détail par comptes réels")

    detail = (
        dep[dep["compte_budget"] == compte_sel]
        .groupby("compte")["montant_ttc"]
        .sum()
        .reset_index()
        .sort_values("montant_ttc", ascending=False)
    )

    detail["% du budget"] = detail["montant_ttc"] / ligne["budget"] * 100
    detail["% du réel"] = detail["montant_ttc"] / ligne["reel"] * 100

    st.dataframe(detail, use_container_width=True)
