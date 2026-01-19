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
    required = {"annee", "compte", "montant_ttc", "poste"}
    if not required.issubset(df.columns):
        st.error(f"Colonnes manquantes dans les dépenses : {required - set(df.columns)}")
        st.stop()

    df["annee"] = df["annee"].astype(float).astype(int)
    df["compte"] = df["compte"].astype(str)
    df["poste"] = df["poste"].astype(str)
    df["montant_ttc"] = df["montant_ttc"].astype(float)
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

    # règle comptable : 621 / 622 sur 4 chiffres, sinon 3
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
# SIDEBAR — CHARGEMENT CSV
# ======================================================
with st.sidebar:
    st.markdown("## 📂 Chargement des données")

    dep_csv = st.file_uploader("Dépenses (CSV)", type="csv")
    bud_csv = st.file_uploader("Budget (CSV)", type="csv")

    if dep_csv:
        df = pd.read_csv(
            dep_csv, sep=None, engine="python",
            on_bad_lines="skip", encoding="utf-8-sig"
        )
        st.session_state.df_dep = normalize_depenses(df)
        st.success("Dépenses chargées")

    if bud_csv:
        df = pd.read_csv(
            bud_csv, sep=None, engine="python",
            on_bad_lines="skip", encoding="utf-8-sig"
        )
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
        [
            "📊 État des dépenses",
            "💰 Budget",
            "📊 Budget vs Réel – Pilotage",
        ]
    )

# ======================================================
# 📊 ONGLET — BUDGET VS RÉEL (AVEC POSTE)
# ======================================================
if page == "📊 Budget vs Réel – Pilotage":

    colf1, colf2, colf3 = st.columns(3)
    with colf1:
        annee = st.selectbox("Année", sorted(df_dep["annee"].unique()))
    with colf2:
        groupes = sorted(df_bud["compte"].str[:2].unique())
        groupe = st.selectbox("Groupe de comptes", ["Tous"] + groupes)
    with colf3:
        only_over = st.checkbox("Uniquement les dépassements")

    dep = df_dep[df_dep["annee"] == annee].copy()
    bud = df_bud[df_bud["annee"] == annee].copy()

    if groupe != "Tous":
        bud = bud[bud["compte"].str.startswith(groupe)]

    if bud.empty:
        st.warning("Aucun budget pour ce filtre.")
        st.stop()

    cles = sorted(bud["compte"].unique(), key=len, reverse=True)

    def map_budget(c):
        for cle in cles:
            if c.startswith(cle):
                return cle
        return "NON BUDGÉTÉ"

    dep["compte_budget"] = dep["compte"].apply(map_budget)

    # --- POSTE DOMINANT PAR COMPTE BUDGÉTAIRE
    postes = (
        dep.groupby(["compte_budget", "poste"])
        .size()
        .reset_index(name="n")
        .sort_values(["compte_budget", "n"], ascending=[True, False])
        .drop_duplicates("compte_budget")
        .set_index("compte_budget")["poste"]
    )

    dep_pos = dep[dep["montant_ttc"] > 0].groupby("compte_budget")["montant_ttc"].sum()
    dep_neg = dep[dep["montant_ttc"] < 0].groupby("compte_budget")["montant_ttc"].sum()

    comp = bud.set_index("compte").copy()
    comp["poste"] = postes
    comp["depenses_brutes"] = dep_pos
    comp["avoirs"] = dep_neg
    comp = comp.fillna(0)

    comp["depenses_nettes"] = comp["depenses_brutes"] + comp["avoirs"]
    comp["ecart_eur"] = comp["depenses_nettes"] - comp["budget"]
    comp["ecart_pct"] = comp["ecart_eur"] / comp["budget"] * 100

    if only_over:
        comp = comp[comp["ecart_eur"] > 0]

    # KPI
    col1, col2, col3, col4, col5, col6 = st.columns(6)
    col1.metric("Budget (€)", f"{comp['budget'].sum():,.0f}".replace(",", " "))
    col2.metric("Dépenses brutes (€)", f"{comp['depenses_brutes'].sum():,.0f}".replace(",", " "))
    col3.metric("Avoirs (€)", f"{comp['avoirs'].sum():,.0f}".replace(",", " "))
    col4.metric("Dépenses nettes (€)", f"{comp['depenses_nettes'].sum():,.0f}".replace(",", " "))
    col5.metric("Écart (€)", f"{comp['ecart_eur'].sum():,.0f}".replace(",", " "))
    col6.metric(
        "Écart (%)",
        f"{(comp['ecart_eur'].sum() / comp['budget'].sum() * 100):.1f} %"
        if comp['budget'].sum() != 0 else "-"
    )

    st.markdown("### Détail Budget vs Réel")
    st.dataframe(
        comp.reset_index()[
            [
                "compte",
                "poste",
                "budget",
                "depenses_brutes",
                "avoirs",
                "depenses_nettes",
                "ecart_eur",
                "ecart_pct",
            ]
        ],
        use_container_width=True,
    )
