import streamlit as st
import pandas as pd

# =========================
# CONFIG
# =========================
st.set_page_config(page_title="Pilotage des charges", layout="wide")
st.title("Pilotage des charges de l’immeuble")

# =========================
# UTILS
# =========================
def normalize_columns(df):
    return df.rename(columns={
        "Année": "annee",
        "Compte": "compte",
        "Montant TTC": "montant_ttc",
        "Budget": "budget",
        "Fournisseur": "fournisseur"
    })

# =========================
# SESSION STATE
# =========================
if "df_depenses" not in st.session_state:
    st.session_state.df_depenses = None

if "df_budget" not in st.session_state:
    st.session_state.df_budget = pd.DataFrame(
        columns=["annee", "compte", "budget"]
    )

# =========================
# IMPORT FICHIERS
# =========================
with st.sidebar:
    st.markdown("## 📂 Chargement des données")

    dep_csv = st.file_uploader("Dépenses (CSV)", type="csv")
    bud_csv = st.file_uploader("Budget (CSV)", type="csv")

    if dep_csv:
        df = pd.read_csv(dep_csv, sep=None, engine="python")
        df.columns = [c.strip().replace("\ufeff", "") for c in df.columns]
        df = normalize_columns(df)
        df["compte"] = df["compte"].astype(str)
        st.session_state.df_depenses = df
        st.success("Dépenses chargées")

    if bud_csv:
        dfb = pd.read_csv(bud_csv, sep=None, engine="python")
        dfb.columns = [c.strip().replace("\ufeff", "") for c in dfb.columns]
        dfb = normalize_columns(dfb)
        dfb["compte"] = dfb["compte"].astype(str)
        st.session_state.df_budget = dfb
        st.success("Budget chargé")

# =========================
# STOP SI PAS DE DONNÉES
# =========================
if st.session_state.df_depenses is None:
    st.info("Veuillez charger les dépenses.")
    st.stop()

df = st.session_state.df_depenses
df_budget = st.session_state.df_budget

# =========================
# SIDEBAR NAVIGATION
# =========================
with st.sidebar:
    st.markdown("## 🧭 Navigation")
    page = st.radio(
        "Choisir une vue",
        ["📊 État des dépenses", "💰 Budget"]
    )

# ======================================================
# 📊 ONGLET 1 — ÉTAT DES DÉPENSES
# ======================================================
if page == "📊 État des dépenses":

    st.subheader("📊 État des dépenses")

    # ---- Filtres
    col1, col2, col3 = st.columns(3)

    with col1:
        annee = st.selectbox(
            "Année",
            sorted(df["annee"].unique())
        )

    df_f = df[df["annee"] == annee]

    with col2:
        comptes = sorted(df_f["compte"].str[:4].unique())
        compte_sel = st.multiselect("Compte", comptes)

    if compte_sel:
        df_f = df_f[df_f["compte"].str[:4].isin(compte_sel)]

    with col3:
        fournisseurs = sorted(df_f["fournisseur"].dropna().unique())
        four_sel = st.multiselect("Fournisseur", fournisseurs)

    if four_sel:
        df_f = df_f[df_f["fournisseur"].isin(four_sel)]

    # ---- Résultat
    st.markdown("### Détail filtré")
    st.dataframe(df_f, use_container_width=True)

    st.markdown("### Total")
    st.metric(
        "Total dépenses (€)",
        f"{df_f['montant_ttc'].sum():,.2f}".replace(",", " ")
    )

# ======================================================
# 💰 ONGLET 2 — BUDGET
# ======================================================
if page == "💰 Budget":

    st.subheader("💰 Gestion du budget")

    if df_budget.empty:
        st.info("Aucun budget chargé. Vous pouvez en créer un.")

    # ---- Filtres budget
    col1, col2, col3 = st.columns(3)

    with col1:
        annee_b = st.selectbox(
            "Année budgétaire",
            sorted(df["annee"].unique())
        )

    with col2:
        groupes = sorted(
            df_budget["compte"].str[:2].unique()
        ) if not df_budget.empty else []
        groupe_sel = st.selectbox("Groupe de comptes", ["Tous"] + groupes)

    with col3:
        comptes_budget = (
            df_budget["compte"].unique().tolist()
            if not df_budget.empty else []
        )
        compte_b = st.selectbox("Compte", ["Tous"] + comptes_budget)

    # ---- Filtrage
    dfb = df_budget[df_budget["annee"] == annee_b]

    if groupe_sel != "Tous":
        dfb = dfb[dfb["compte"].str.startswith(groupe_sel)]

    if compte_b != "Tous":
        dfb = dfb[dfb["compte"] == compte_b]

    # ---- Édition
    st.markdown("### ✏️ Ajouter / Modifier / Supprimer")

    df_edit = st.data_editor(
        dfb,
        num_rows="dynamic",
        use_container_width=True
    )

    # ---- Reconstruction budget complet
    df_budget_other = df_budget[df_budget["annee"] != annee_b]
    df_budget_new = pd.concat(
        [df_budget_other, df_edit],
        ignore_index=True
    )

    st.session_state.df_budget = df_budget_new

    # ---- Export
    st.markdown("### 💾 Sauvegarde")
    export_file = f"budget_{annee_b}.csv"
    df_budget_new.to_csv(export_file, index=False, encoding="utf-8")

    with open(export_file, "rb") as f:
        st.download_button(
            "📥 Télécharger le budget",
            f,
            file_name=export_file
        )

# =========================
# FOOTER
# =========================
st.markdown("---")
st.caption("Outil de pilotage – Conseil syndical / Copropriété")
