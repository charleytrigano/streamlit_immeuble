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
def normalize_columns(df: pd.DataFrame) -> pd.DataFrame:
    return df.rename(columns={
        "Année": "annee",
        "Compte": "compte",
        "Montant TTC": "montant_ttc",
        "Budget": "budget",
        "Fournisseur": "fournisseur",
        "Comptes généraux": "compte_general"
    })

def normalize_budget_account(compte: str) -> str:
    """
    Règle comptable :
    - 621x / 622x → 4 chiffres
    - autres → 3 chiffres
    """
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

    # --- Chargement dépenses
    if dep_csv:
        df = pd.read_csv(dep_csv, sep=None, engine="python")
        df.columns = [c.strip().replace("\ufeff", "") for c in df.columns]
        df = normalize_columns(df)

        df["annee"] = df["annee"].astype(int)
        df["compte"] = df["compte"].astype(str)

        st.session_state.df_depenses = df
        st.success("Dépenses chargées")

    # --- Chargement budget
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
# SIDEBAR — NAVIGATION
# ======================================================
with st.sidebar:
    st.markdown("## 🧭 Navigation")
    page = st.radio("Vue", ["📊 État des dépenses", "💰 Budget"])

# ======================================================
# 📊 ONGLET 1 — ÉTAT DES DÉPENSES
# ======================================================
if page == "📊 État des dépenses":

    st.subheader("📊 État des dépenses")

    col1, col2, col3 = st.columns(3)

    with col1:
        annee = st.selectbox("Année", sorted(df_dep["annee"].unique()))

    df_f = df_dep[df_dep["annee"] == annee].copy()

    with col2:
        comptes = sorted(df_f["compte"].apply(normalize_budget_account).unique())
        compte_sel = st.multiselect("Compte", comptes)

    if compte_sel:
        df_f["compte_budget"] = df_f["compte"].apply(normalize_budget_account)
        df_f = df_f[df_f["compte_budget"].isin(compte_sel)]

    with col3:
        fournisseurs = sorted(df_f["fournisseur"].dropna().unique())
        four_sel = st.multiselect("Fournisseur", fournisseurs)

    if four_sel:
        df_f = df_f[df_f["fournisseur"].isin(four_sel)]

    st.markdown("### Détail des dépenses")
    st.dataframe(df_f, use_container_width=True)

    st.metric(
        "Total (€)",
        f"{df_f['montant_ttc'].sum():,.2f}".replace(",", " ")
    )

# ======================================================
# 💰 ONGLET 2 — BUDGET
# ======================================================
if page == "💰 Budget":

    st.subheader("💰 Gestion du budget")

    col1, col2, col3 = st.columns(3)

    with col1:
        annee_b = st.selectbox(
            "Année budgétaire",
            sorted(df_dep["annee"].unique())
        )

    with col2:
        groupes = sorted(df_budget["compte"].str[:2].unique()) if not df_budget.empty else []
        groupe_sel = st.selectbox("Groupe de comptes", ["Tous"] + groupes)

    with col3:
        comptes = sorted(df_budget["compte"].unique()) if not df_budget.empty else []
        compte_sel = st.selectbox("Compte", ["Tous"] + comptes)

    # Filtrage budget
    dfb = df_budget[df_budget["annee"] == annee_b].copy()

    if groupe_sel != "Tous":
        dfb = dfb[dfb["compte"].str.startswith(groupe_sel)]

    if compte_sel != "Tous":
        dfb = dfb[dfb["compte"] == compte_sel]

    st.markdown("### ✏️ Ajouter / Modifier / Supprimer")

    df_edit = st.data_editor(
        dfb,
        num_rows="dynamic",
        use_container_width=True
    )

    # 👉 L’ANNÉE ÉDITÉE EST SOURCE DE VÉRITÉ
    df_budget_new = pd.concat(
        [
            df_budget[df_budget["annee"] != annee_b],
            df_edit
        ],
        ignore_index=True
    )

    st.session_state.df_budget = df_budget_new

    # Sauvegarde
    st.markdown("### 💾 Sauvegarde")

    export_file = f"budget_{annee_b}.csv"
    df_budget_new.to_csv(export_file, index=False, encoding="utf-8")

    with open(export_file, "rb") as f:
        st.download_button(
            "📥 Télécharger le budget",
            f,
            file_name=export_file
        )

# ======================================================
# FOOTER
# ======================================================
st.markdown("---")
st.caption("Outil de pilotage – Conseil syndical / Copropriété")
