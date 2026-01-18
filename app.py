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
    df["montant_ttc"] = df["montant_ttc"].astype(float)
    return df


def normalize_budget(df):
    df = df.rename(columns={
        "Annee": "annee",
        "compte": "compte",
        "budget": "budget",
    })
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
        [
            "📊 État des dépenses",
            "💰 Budget",
            "📊 Budget vs Réel – Pilotage",
        ]
    )

# ======================================================
# 📊 ONGLET — BUDGET VS RÉEL (CORRIGÉ)
# ======================================================
if page == "📊 Budget vs Réel – Pilotage":

    st.subheader("📊 Budget vs Réel – Pilotage")

    colf1, colf2 = st.columns(2)
    with colf1:
        annee = st.selectbox("Année", sorted(df_dep["annee"].unique()))
    with colf2:
        only_over = st.checkbox("Uniquement les dépassements")

    dep = df_dep[df_dep["annee"] == annee].copy()
    bud = df_budget[df_budget["annee"] == annee].copy()

    if bud.empty:
        st.warning("Aucun budget pour cette année.")
        st.stop()

    cles_budget = sorted(bud["compte"].unique(), key=len, reverse=True)

    def map_budget(compte):
        for cle in cles_budget:
            if str(compte).startswith(cle):
                return cle
        return "NON BUDGÉTÉ"

    dep["compte_budget"] = dep["compte"].apply(map_budget)

    # --- Séparation explicite
    dep_pos = dep[dep["montant_ttc"] > 0]
    dep_neg = dep[dep["montant_ttc"] < 0]

    # --- Agrégations
    reel_dep = dep_pos.groupby("compte_budget")["montant_ttc"].sum().reset_index(name="depenses_brutes")
    avoirs = dep_neg.groupby("compte_budget")["montant_ttc"].sum().reset_index(name="avoirs")

    comp = bud.merge(reel_dep, left_on="compte", right_on="compte_budget", how="left")
    comp = comp.merge(avoirs, left_on="compte", right_on="compte_budget", how="left")

    comp["depenses_brutes"] = comp["depenses_brutes"].fillna(0)
    comp["avoirs"] = comp["avoirs"].fillna(0)

    # 🔑 DÉPENSES NETTES
    comp["depenses_nettes"] = comp["depenses_brutes"] + comp["avoirs"]

    # 🔑 ÉCART CORRECT
    comp["ecart_eur"] = comp["depenses_nettes"] - comp["budget"]
    comp["ecart_pct"] = comp.apply(
        lambda r: (r["ecart_eur"] / r["budget"] * 100) if r["budget"] != 0 else 0,
        axis=1,
    )

    if only_over:
        comp = comp[comp["ecart_eur"] > 0]

    # --- KPI globaux (NETS)
    total_budget = comp["budget"].sum()
    total_dep_nettes = comp["depenses_nettes"].sum()
    total_avoirs = comp["avoirs"].sum()

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Budget (€)", f"{total_budget:,.0f}".replace(",", " "))
    col2.metric("Dépenses nettes (€)", f"{total_dep_nettes:,.0f}".replace(",", " "))
    col3.metric("Avoirs (€)", f"{total_avoirs:,.0f}".replace(",", " "))
    col4.metric("Écart (€)", f"{(total_dep_nettes - total_budget):,.0f}".replace(",", " "))

    st.markdown("### Détail Budget vs Réel")
    st.dataframe(
        comp[
            [
                "compte",
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
