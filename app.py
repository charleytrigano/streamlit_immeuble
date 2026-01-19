import streamlit as st
import pandas as pd
import unicodedata

# ======================================================
# CONFIG
# ======================================================
st.set_page_config(page_title="Pilotage des charges", layout="wide")
st.title("Pilotage des charges de l’immeuble")

# ======================================================
# OUTILS ROBUSTES
# ======================================================
def clean_columns(df: pd.DataFrame) -> pd.DataFrame:
    def normalize(col):
        col = str(col).strip().lower()
        col = unicodedata.normalize("NFKD", col).encode("ascii", "ignore").decode()
        col = col.replace(" ", "_")
        return col
    df.columns = [normalize(c) for c in df.columns]
    return df

# ======================================================
# NORMALISATION
# ======================================================
def normalize_depenses(df: pd.DataFrame) -> pd.DataFrame:
    df = clean_columns(df)

    required = {"annee", "compte", "montant_ttc"}
    missing = required - set(df.columns)
    if missing:
        st.error(f"Colonnes manquantes dans le fichier dépenses : {missing}")
        st.stop()

    df["annee"] = df["annee"].astype(float).astype(int)
    df["compte"] = df["compte"].astype(str)
    df["montant_ttc"] = df["montant_ttc"].astype(float)

    return df


def normalize_budget(df: pd.DataFrame) -> pd.DataFrame:
    df = clean_columns(df)

    required = {"annee", "compte", "budget"}
    missing = required - set(df.columns)
    if missing:
        st.error(f"Colonnes manquantes dans le fichier budget : {missing}")
        st.stop()

    df["annee"] = df["annee"].astype(float).astype(int)
    df["compte"] = df["compte"].astype(str)
    df["budget"] = df["budget"].astype(float)

    # règle comptable
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
# SIDEBAR — CHARGEMENT CSV ROBUSTE
# ======================================================
with st.sidebar:
    st.markdown("## 📂 Chargement des données")

    dep_csv = st.file_uploader("Dépenses (CSV)", type="csv")
    bud_csv = st.file_uploader("Budget (CSV)", type="csv")

    if dep_csv:
        df = pd.read_csv(
            dep_csv,
            sep=None,
            engine="python",
            on_bad_lines="skip",
            encoding="utf-8-sig",
        )
        st.session_state.df_depenses = normalize_depenses(df)
        st.success("Dépenses chargées")

    if bud_csv:
        df = pd.read_csv(
            bud_csv,
            sep=None,
            engine="python",
            on_bad_lines="skip",
            encoding="utf-8-sig",
        )
        st.session_state.df_budget = normalize_budget(df)
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
        [
            "📊 État des dépenses",
            "💰 Budget",
            "📊 Budget vs Réel – Pilotage",
        ]
    )

# ======================================================
# 📊 ONGLET 1 — ÉTAT DES DÉPENSES
# ======================================================
if page == "📊 État des dépenses":

    annee = st.selectbox("Année", sorted(df_dep["annee"].unique()))
    df_a = df_dep[df_dep["annee"] == annee].copy()

    dep_pos = df_a[df_a["montant_ttc"] > 0]
    dep_neg = df_a[df_a["montant_ttc"] < 0]

    col1, col2, col3 = st.columns(3)
    col1.metric("Dépenses brutes (€)", f"{dep_pos['montant_ttc'].sum():,.0f}".replace(",", " "))
    col2.metric("Avoirs (€)", f"{dep_neg['montant_ttc'].sum():,.0f}".replace(",", " "))
    col3.metric("Dépenses nettes (€)", f"{df_a['montant_ttc'].sum():,.0f}".replace(",", " "))

    st.data_editor(df_a, num_rows="dynamic", use_container_width=True)

# ======================================================
# 💰 ONGLET 2 — BUDGET
# ======================================================
if page == "💰 Budget":

    annee_b = st.selectbox("Année budgétaire", sorted(df_budget["annee"].unique()))
    dfb = df_budget[df_budget["annee"] == annee_b]

    st.metric("Budget total (€)", f"{dfb['budget'].sum():,.0f}".replace(",", " "))
    st.data_editor(dfb, num_rows="dynamic", use_container_width=True)

# ======================================================
# 📊 ONGLET 3 — BUDGET VS RÉEL
# ======================================================
if page == "📊 Budget vs Réel – Pilotage":

    annee = st.selectbox("Année", sorted(df_dep["annee"].unique()))
    dep = df_dep[df_dep["annee"] == annee]
    bud = df_budget[df_budget["annee"] == annee]

    cles_budget = sorted(bud["compte"].unique(), key=len, reverse=True)

    def map_budget(c):
        for cle in cles_budget:
            if c.startswith(cle):
                return cle
        return "NON BUDGÉTÉ"

    dep["compte_budget"] = dep["compte"].apply(map_budget)

    dep_pos = dep[dep["montant_ttc"] > 0]
    dep_neg = dep[dep["montant_ttc"] < 0]

    reel = dep_pos.groupby("compte_budget")["montant_ttc"].sum()
    avoirs = dep_neg.groupby("compte_budget")["montant_ttc"].sum()

    comp = bud.set_index("compte").copy()
    comp["depenses_brutes"] = reel
    comp["avoirs"] = avoirs
    comp = comp.fillna(0)
    comp["depenses_nettes"] = comp["depenses_brutes"] + comp["avoirs"]
    comp["ecart"] = comp["depenses_nettes"] - comp["budget"]

    st.dataframe(comp.reset_index(), use_container_width=True)
