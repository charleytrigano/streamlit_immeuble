import streamlit as st
import pandas as pd
import unicodedata

# ======================================================
# CONFIG
# ======================================================
st.set_page_config(page_title="Pilotage des charges", layout="wide")
st.title("Pilotage des charges de l’immeuble")

# ======================================================
# OUTILS
# ======================================================
def clean_columns(df: pd.DataFrame) -> pd.DataFrame:
    def norm(c):
        c = str(c).strip().lower()
        c = unicodedata.normalize("NFKD", c).encode("ascii", "ignore").decode()
        return c.replace(" ", "_")
    df.columns = [norm(c) for c in df.columns]
    return df

# ======================================================
# NORMALISATION
# ======================================================
def normalize_depenses(df: pd.DataFrame) -> pd.DataFrame:
    df = clean_columns(df)

    if "poste" not in df.columns:
        df["poste"] = "Non renseigné"

    required = {"annee", "compte", "montant_ttc"}
    if not required.issubset(df.columns):
        st.error(f"Colonnes manquantes dans les dépenses : {required - set(df.columns)}")
        st.stop()

    df["annee"] = df["annee"].astype(float).astype(int)
    df["compte"] = df["compte"].astype(str)
    df["poste"] = df["poste"].astype(str)
    df["montant_ttc"] = df["montant_ttc"].astype(float)

    if "fournisseur" in df.columns:
        df["fournisseur"] = df["fournisseur"].astype(str)
    else:
        df["fournisseur"] = "Non renseigné"

    return df


def normalize_budget(df: pd.DataFrame) -> pd.DataFrame:
    df = clean_columns(df)

    required = {"annee", "compte", "budget"}
    if not required.issubset(df.columns):
        st.error(f"Colonnes manquantes dans le budget : {required - set(df.columns)}")
        st.stop()

    df["annee"] = df["annee"].astype(float).astype(int)
    df["compte"] = df["compte"].astype(str)
    df["budget"] = df["budget"].astype(float)

    df["compte"] = df["compte"].apply(
        lambda x: x[:4] if x.startswith(("621", "622")) else x[:3]
    )
    return df

# ======================================================
# SESSION STATE
# ======================================================
if "df_dep" not in st.session_state:
    st.session_state.df_dep = None
if "df_bud" not in st.session_state:
    st.session_state.df_bud = None

# ======================================================
# SIDEBAR — CHARGEMENT
# ======================================================
with st.sidebar:
    st.markdown("## 📂 Chargement des données")
    dep_csv = st.file_uploader("Dépenses (CSV)", type="csv")
    bud_csv = st.file_uploader("Budget (CSV)", type="csv")

    if dep_csv:
        df = pd.read_csv(dep_csv, sep=None, engine="python", on_bad_lines="skip", encoding="utf-8-sig")
        st.session_state.df_dep = normalize_depenses(df)
        st.success("Dépenses chargées")

    if bud_csv:
        df = pd.read_csv(bud_csv, sep=None, engine="python", on_bad_lines="skip", encoding="utf-8-sig")
        st.session_state.df_bud = normalize_budget(df)
        st.success("Budget chargé")

if st.session_state.df_dep is None or st.session_state.df_bud is None:
    st.info("Veuillez charger les dépenses et le budget.")
    st.stop()

df_dep = st.session_state.df_dep
df_bud = st.session_state.df_bud

# ======================================================
# NAVIGATION
# ======================================================
with st.sidebar:
    page = st.radio(
        "Navigation",
        ["📊 État des dépenses", "💰 Budget", "📊 Budget vs Réel – Pilotage"]
    )

# ======================================================
# 📊 ONGLET 1 — ÉTAT DES DÉPENSES (AVEC FILTRES)
# ======================================================
if page == "📊 État des dépenses":

    # ---------- FILTRES
    colf1, colf2, colf3 = st.columns(3)
    with colf1:
        annee = st.selectbox("Année", sorted(df_dep["annee"].unique()))
    with colf2:
        groupes = sorted(df_dep["compte"].str[:2].unique())
        groupe = st.selectbox("Groupe de comptes", ["Tous"] + groupes)
    with colf3:
        type_flux = st.selectbox("Type", ["Tous", "Dépenses", "Avoirs"])

    df_f = df_dep[df_dep["annee"] == annee].copy()

    if groupe != "Tous":
        df_f = df_f[df_f["compte"].str.startswith(groupe)]

    fournisseurs = ["Tous"] + sorted(df_f["fournisseur"].unique())
    postes = ["Tous"] + sorted(df_f["poste"].unique())

    colf4, colf5 = st.columns(2)
    with colf4:
        fournisseur = st.selectbox("Fournisseur", fournisseurs)
    with colf5:
        poste = st.selectbox("Poste", postes)

    if fournisseur != "Tous":
        df_f = df_f[df_f["fournisseur"] == fournisseur]

    if poste != "Tous":
        df_f = df_f[df_f["poste"] == poste]

    if type_flux == "Dépenses":
        df_f = df_f[df_f["montant_ttc"] > 0]
    elif type_flux == "Avoirs":
        df_f = df_f[df_f["montant_ttc"] < 0]

    # ---------- KPI
    dep_pos = df_f[df_f["montant_ttc"] > 0]["montant_ttc"].sum()
    dep_neg = df_f[df_f["montant_ttc"] < 0]["montant_ttc"].sum()

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Dépenses brutes (€)", f"{dep_pos:,.0f}".replace(",", " "))
    col2.metric("Avoirs (€)", f"{dep_neg:,.0f}".replace(",", " "))
    col3.metric("Dépenses nettes (€)", f"{dep_pos + dep_neg:,.0f}".replace(",", " "))
    col4.metric("Lignes", len(df_f))

    # ---------- ÉDITION
    st.markdown("### ✏️ Ajouter / Modifier / Supprimer des dépenses")

    df_edit = st.data_editor(df_f, num_rows="dynamic", use_container_width=True)

    df_other = df_dep.drop(df_f.index)
    st.session_state.df_dep = pd.concat([df_other, df_edit], ignore_index=True)

    st.download_button(
        "📥 Télécharger les dépenses",
        st.session_state.df_dep.to_csv(index=False).encode("utf-8"),
        file_name="base_depenses_immeuble.csv",
        mime="text/csv",
    )
