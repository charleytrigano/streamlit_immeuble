import streamlit as st
import pandas as pd

# ======================================================
# CONFIG
# ======================================================
st.set_page_config(page_title="Pilotage des charges", layout="wide")
st.title("Pilotage des charges de l’immeuble")

# ======================================================
# NORMALISATION
# ======================================================
def normalize_depenses(df):
    df = df.rename(columns={
        "Annee": "annee",
        "Compte": "compte",
        "Poste": "poste",
        "Fournisseur": "fournisseur",
        "Date": "date",
        "Montant TTC": "montant_ttc",
        "Type": "type",
        "Recurrent": "recurrent",
        "Commentaire": "commentaire",
    })
    df["annee"] = df["annee"].astype(float).astype(int)
    df["compte"] = df["compte"].astype(str)
    return df

def normalize_budget(df):
    df = df.rename(columns={
        "Annee": "annee",
        "compte": "compte",
        "budget": "budget",
    })
    df["annee"] = df["annee"].astype(float).astype(int)
    df["compte"] = df["compte"].astype(str)
    df["compte"] = df["compte"].apply(
        lambda x: x[:4] if x.startswith(("621", "622")) else x[:3]
    )
    return df

# ======================================================
# SESSION STATE
# ======================================================
if "df_depenses" not in st.session_state:
    st.session_state.df_depenses = None
if "df_budget" not in st.session_state:
    st.session_state.df_budget = None

# ======================================================
# SIDEBAR — CHARGEMENT
# ======================================================
with st.sidebar:
    st.markdown("## 📂 Chargement des données")
    dep_csv = st.file_uploader("Dépenses (CSV)", type="csv")
    bud_csv = st.file_uploader("Budget (CSV)", type="csv")

    if dep_csv:
        st.session_state.df_depenses = normalize_depenses(pd.read_csv(dep_csv))
        st.success("Dépenses chargées")

    if bud_csv:
        st.session_state.df_budget = normalize_budget(pd.read_csv(bud_csv))
        st.success("Budget chargé")

# ======================================================
# STOP
# ======================================================
if st.session_state.df_depenses is None or st.session_state.df_budget is None:
    st.info("Veuillez charger les dépenses et le budget.")
    st.stop()

df_dep = st.session_state.df_depenses
df_budget = st.session_state.df_budget

# ======================================================
# NAVIGATION
# ======================================================
with st.sidebar:
    page = st.radio(
        "Navigation",
        ["📊 État des dépenses", "💰 Budget", "📊 Budget vs Réel – Analyse"]
    )

# ======================================================
# 📊 ONGLET 1 — ÉTAT DES DÉPENSES
# ======================================================
if page == "📊 État des dépenses":

    annee = st.selectbox("Année", sorted(df_dep["annee"].unique()))
    df_a = df_dep[df_dep["annee"] == annee].copy()

    col1, col2, col3 = st.columns(3)
    col1.metric("Total dépenses (€)", f"{df_a['montant_ttc'].sum():,.2f}".replace(",", " "))
    col2.metric("Lignes", len(df_a))
    col3.metric("Fournisseurs", df_a["fournisseur"].nunique())

    st.dataframe(df_a, use_container_width=True)

# ======================================================
# 💰 ONGLET 2 — BUDGET
# ======================================================
if page == "💰 Budget":

    annee_b = st.selectbox("Année budgétaire", sorted(df_budget["annee"].unique()))

    # KPI CALCULÉ SUR LA BASE COMPLÈTE
    budget_total = df_budget[df_budget["annee"] == annee_b]["budget"].sum()

    dfb = df_budget[df_budget["annee"] == annee_b].copy()

    col1, col2, col3 = st.columns(3)
    col1.metric("Budget total (€)", f"{budget_total:,.2f}".replace(",", " "))
    col2.metric("Comptes", len(dfb))
    col3.metric("Groupes", dfb["compte"].str[:2].nunique())

    st.markdown("### ✏️ Ajouter / Modifier / Supprimer")
    df_edit = st.data_editor(dfb, num_rows="dynamic", use_container_width=True)

    st.session_state.df_budget = pd.concat(
        [df_budget[df_budget["annee"] != annee_b], df_edit],
        ignore_index=True
    )

# ======================================================
# 📊 ONGLET 3 — BUDGET VS RÉEL
# ======================================================
if page == "📊 Budget vs Réel – Analyse":

    annee = st.selectbox("Année analysée", sorted(df_dep["annee"].unique()))

    dep = df_dep[df_dep["annee"] == annee].copy()
    dep["compte"] = dep["compte"].astype(str)

    bud = df_budget[df_budget["annee"] == annee].copy()

    cles_budget = sorted(bud["compte"].unique(), key=len, reverse=True)

    def map_budget(compte):
        for cle in cles_budget:
            if compte.startswith(cle):
                return cle
        return "NON BUDGÉTÉ"

    dep["compte_budget"] = dep["compte"].apply(map_budget)

    reel = dep.groupby("compte_budget")["montant_ttc"].sum().reset_index(name="reel")

    comp = bud.merge(
        reel,
        left_on="compte",
        right_on="compte_budget",
        how="left"
    )

    comp["reel"] = comp["reel"].fillna(0)
    comp["ecart_eur"] = comp["reel"] - comp["budget"]
    comp["ecart_pct"] = comp.apply(
        lambda r: (r["ecart_eur"] / r["budget"] * 100)
        if r["budget"] != 0 else 0,
        axis=1
    )

    st.dataframe(
        comp[["compte", "budget", "reel", "ecart_eur", "ecart_pct"]],
        use_container_width=True
    )

# ======================================================
# FOOTER
# ======================================================
st.markdown("---")
st.caption("Outil de pilotage – Conseil syndical / Copropriété")
