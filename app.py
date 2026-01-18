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
def normalize_depenses(df: pd.DataFrame) -> pd.DataFrame:
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

    required = {"annee", "compte", "montant_ttc"}
    if not required.issubset(df.columns):
        raise ValueError(f"Colonnes manquantes : {required - set(df.columns)}")

    df["annee"] = df["annee"].astype(float).astype(int)
    df["compte"] = df["compte"].astype(str)

    return df


def normalize_budget(df: pd.DataFrame) -> pd.DataFrame:
    df = df.rename(columns={
        "Annee": "annee",
        "compte": "compte",
        "budget": "budget",
    })

    required = {"annee", "compte", "budget"}
    if not required.issubset(df.columns):
        raise ValueError(f"Colonnes manquantes : {required - set(df.columns)}")

    df["annee"] = df["annee"].astype(float).astype(int)
    df["compte"] = df["compte"].astype(str)

    # Règle comptable
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
        try:
            df = pd.read_csv(dep_csv)
            df = normalize_depenses(df)
            st.session_state.df_depenses = df
            st.success("Dépenses chargées")
        except Exception as e:
            st.error(str(e))
            st.stop()

    if bud_csv:
        try:
            dfb = pd.read_csv(bud_csv)
            dfb = normalize_budget(dfb)
            st.session_state.df_budget = dfb
            st.success("Budget chargé")
        except Exception as e:
            st.error(str(e))
            st.stop()

# ======================================================
# STOP SI DONNÉES MANQUANTES
# ======================================================
if st.session_state.df_depenses is None or st.session_state.df_budget is None:
    st.info("Veuillez charger les dépenses et le budget.")
    st.stop()

df_dep = st.session_state.df_depenses
df_budget = st.session_state.df_budget

# ======================================================
# ANALYSE — BUDGET VS RÉEL AVEC COMPARAISON DÉTAILLÉE
# ======================================================
st.markdown("## 📊 Analyse Budget vs Réel")

annee = st.selectbox("Année analysée", sorted(df_dep["annee"].unique()))

dep = df_dep[df_dep["annee"] == annee].copy()
bud = df_budget[df_budget["annee"] == annee].copy()

# Clés budgétaires = source de vérité
cles_budget = sorted(bud["compte"].unique(), key=len, reverse=True)

def map_budget(compte_reel):
    for cle in cles_budget:
        if compte_reel.startswith(cle):
            return cle
    return "NON BUDGETÉ"

dep["compte_budget"] = dep["compte"].apply(map_budget)

# ===== Vue macro
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

# ===== Drill-down explicatif
st.markdown("## 🔍 Détail par compte réel")

compte_sel = st.selectbox("Compte budgété", macro["compte"].tolist())

ligne = macro[macro["compte"] == compte_sel].iloc[0]

detail = (
    dep[dep["compte_budget"] == compte_sel]
    .groupby("compte")["montant_ttc"]
    .sum()
    .reset_index()
    .sort_values("montant_ttc", ascending=False)
)

detail["% du budget"] = detail["montant_ttc"] / ligne["budget"] * 100
detail["% du réel"] = (
    detail["montant_ttc"] / ligne["reel"] * 100 if ligne["reel"] != 0 else 0
)

st.dataframe(detail, use_container_width=True)
