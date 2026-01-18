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
    st.info("Veuillez charger le fichier des dépenses.")
    st.stop()

df_dep = st.session_state.df_depenses
df_budget = st.session_state.df_budget

# ======================================================
# NAVIGATION
# ======================================================
with st.sidebar:
    page = st.radio(
        "Vue",
        ["📊 État des dépenses", "💰 Budget", "📊 Budget vs Réel"]
    )

# ======================================================
# 📊 ÉTAT DES DÉPENSES
# ======================================================
if page == "📊 État des dépenses":

    annee = st.selectbox("Année", sorted(df_dep["annee"].unique()))
    df_a = df_dep[df_dep["annee"] == annee].copy()

    total_dep = df_a["montant_ttc"].sum()

    # KPI
    col1, col2, col3 = st.columns(3)
    col1.metric("Total dépenses (€)", f"{total_dep:,.2f}".replace(",", " "))
    col2.metric("Nombre de lignes", len(df_a))
    col3.metric("Nombre de fournisseurs", df_a["fournisseur"].nunique())

    # Tableau détail
    st.markdown("### Détail des dépenses")
    st.dataframe(df_a, use_container_width=True)

    # Tableau par groupes de comptes
    st.markdown("### Dépenses par groupe de comptes")
    df_a["groupe"] = df_a["compte"].str[:2]

    grp = (
        df_a.groupby("groupe")["montant_ttc"]
        .sum()
        .reset_index()
        .sort_values("montant_ttc", ascending=False)
    )
    grp["% du total"] = grp["montant_ttc"] / total_dep * 100
    st.dataframe(grp, use_container_width=True)

# ======================================================
# 💰 BUDGET
# ======================================================
if page == "💰 Budget":

    annee_b = st.selectbox("Année budgétaire", sorted(df_dep["annee"].unique()))
    dfb = df_budget[df_budget["annee"] == annee_b].copy()

    # KPI Budget
    col1, col2, col3 = st.columns(3)
    col1.metric("Budget total (€)", f"{dfb['budget'].sum():,.2f}".replace(",", " "))
    col2.metric("Comptes budgétés", len(dfb))
    col3.metric("Groupes couverts", dfb["compte"].str[:2].nunique())

    st.markdown("### ✏️ Budget éditable")
    df_edit = st.data_editor(dfb, num_rows="dynamic", use_container_width=True)

    # 👉 L’ANNÉE ÉDITÉE EST SOURCE DE VÉRITÉ
    df_budget_new = pd.concat(
        [
            df_budget[df_budget["annee"] != annee_b],
            df_edit
        ],
        ignore_index=True
    )
    st.session_state.df_budget = df_budget_new

# ======================================================
# 📊 BUDGET VS RÉEL (CORRIGÉ DÉFINITIVEMENT)
# ======================================================
if page == "📊 Budget vs Réel":

    annee_c = st.selectbox("Année analysée", sorted(df_dep["annee"].unique()))

    dep = df_dep[df_dep["annee"] == annee_c].copy()
    bud = df_budget[df_budget["annee"] == annee_c].copy()

    if bud.empty:
        st.warning("Aucun budget pour cette année.")
        st.stop()

    # Clés budgétaires = SOURCE DE VÉRITÉ
    cles_budget = sorted(bud["compte"].unique(), key=len, reverse=True)

    def map_budget(compte_reel):
        for cle in cles_budget:
            if compte_reel.startswith(cle):
                return cle
        return "NON BUDGÉTÉ"

    dep["cle_budget"] = dep["compte"].apply(map_budget)

    # Réel agrégé
    reel = (
        dep.groupby("cle_budget")["montant_ttc"]
        .sum()
        .reset_index(name="reel")
    )

    # 🔑 JOINTURE EN PARTANT DU BUDGET (CORRECTION CLÉ)
    comp = bud.merge(
        reel,
        left_on="compte",
        right_on="cle_budget",
        how="left"
    )

    comp["reel"] = comp["reel"].fillna(0)
    comp["ecart_eur"] = comp["reel"] - comp["budget"]
    comp["ecart_pct"] = comp.apply(
        lambda r: (r["ecart_eur"] / r["budget"] * 100)
        if r["budget"] != 0 else None,
        axis=1
    )

    # KPI Budget vs Réel
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total réel (€)", f"{comp['reel'].sum():,.2f}".replace(",", " "))
    col2.metric("Total budget (€)", f"{comp['budget'].sum():,.2f}".replace(",", " "))
    col3.metric("Écart global (€)", f"{comp['ecart_eur'].sum():,.2f}".replace(",", " "))
    col4.metric(
        "Postes en dépassement",
        int((comp["ecart_eur"] > 0).sum())
    )

    st.dataframe(
        comp[["compte", "reel", "budget", "ecart_eur", "ecart_pct"]],
        use_container_width=True
    )

# ======================================================
# FOOTER
# ======================================================
st.markdown("---")
st.caption("Outil de pilotage – Conseil syndical / Copropriété")
