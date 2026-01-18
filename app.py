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
    df.columns = (
        df.columns
        .str.strip()
        .str.lower()
        .str.replace("é", "e")
        .str.replace("è", "e")
        .str.replace("ê", "e")
        .str.replace("à", "a")
        .str.replace(" ", "_")
    )
    return df.rename(columns={
        "annee": "annee",
        "compte": "compte",
        "montant_ttc": "montant_ttc",
        "montant": "montant_ttc",
        "budget": "budget",
        "fournisseur": "fournisseur",
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
    st.session_state.df_budget = pd.DataFrame(columns=["annee", "compte", "budget"])

# ======================================================
# SIDEBAR — CHARGEMENT
# ======================================================
with st.sidebar:
    st.markdown("## 📂 Chargement des données")

    dep_csv = st.file_uploader("Dépenses (CSV)", type="csv")
    bud_csv = st.file_uploader("Budget (CSV)", type="csv")

    # ---------- Dépenses ----------
    if dep_csv:
        df = pd.read_csv(dep_csv, sep=None, engine="python")
        df = normalize_columns(df)

        if "annee" not in df.columns:
            st.error(
                f"Colonnes détectées : {', '.join(df.columns)}\n\n"
                "Impossible d’identifier la colonne Année."
            )
            st.stop()

        df["annee"] = df["annee"].astype(float).astype(int)
        df["compte"] = df["compte"].astype(str)

        st.session_state.df_depenses = df
        st.success("Dépenses chargées")

    # ---------- Budget ----------
    if bud_csv:
        dfb = pd.read_csv(bud_csv, sep=None, engine="python")
        dfb = normalize_columns(dfb)

        if not {"annee", "compte", "budget"}.issubset(dfb.columns):
            st.error(
                f"Colonnes détectées : {', '.join(dfb.columns)}\n\n"
                "Le budget doit contenir : annee, compte, budget."
            )
            st.stop()

        dfb["annee"] = dfb["annee"].astype(float).astype(int)
        dfb["compte"] = dfb["compte"].astype(str)
        dfb["compte"] = dfb["compte"].apply(normalize_budget_account)

        st.session_state.df_budget = dfb[["annee", "compte", "budget"]]
        st.success("Budget chargé")

# ======================================================
# STOP
# ======================================================
if st.session_state.df_depenses is None:
    st.stop()

df_dep = st.session_state.df_depenses
df_budget = st.session_state.df_budget

# ======================================================
# ANALYSE — BUDGET VS RÉEL AVEC DÉTAIL
# ======================================================
st.markdown("## 📊 Analyse Budget vs Réel")

annee = st.selectbox("Année analysée", sorted(df_dep["annee"].unique()))

dep = df_dep[df_dep["annee"] == annee].copy()
bud = df_budget[df_budget["annee"] == annee].copy()

if bud.empty:
    st.warning("Aucun budget pour cette année.")
    st.stop()

cles_budget = sorted(bud["compte"].unique(), key=len, reverse=True)

def map_budget(compte):
    for cle in cles_budget:
        if compte.startswith(cle):
            return cle
    return "NON BUDGETE"

dep["compte_budget"] = dep["compte"].apply(map_budget)

# ---- Vue macro
reel_macro = dep.groupby("compte_budget")["montant_ttc"].sum().reset_index(name="reel")

macro = bud.merge(
    reel_macro,
    left_on="compte",
    right_on="compte_budget",
    how="left"
)

macro["reel"] = macro["reel"].fillna(0)
macro["ecart_eur"] = macro["reel"] - macro["budget"]
macro["ecart_pct"] = macro["ecart_eur"] / macro["budget"] * 100

st.dataframe(
    macro[["compte", "budget", "reel", "ecart_eur", "ecart_pct"]],
    use_container_width=True
)

# ---- Drill-down
st.markdown("## 🔍 Détail par compte")

compte_sel = st.selectbox("Compte budgété", macro["compte"].tolist())

ligne = macro[macro["compte"] == compte_sel].iloc[0]

detail = (
    dep[dep["compte_budget"] == compte_sel]
    .groupby("compte")["montant_ttc"]
    .sum()
    .reset_index()
    .sort_values("montant_ttc", ascending=False)
)

detail["% du budget"] = detail["montant_ttc"] / ligne["budget"]
detail["% du reel"] = (
    detail["montant_ttc"] / ligne["reel"] if ligne["reel"] != 0 else 0
)

st.dataframe(detail, use_container_width=True)
