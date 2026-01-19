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
# SIDEBAR — CHARGEMENT ROBUSTE CSV
# ======================================================
with st.sidebar:
    st.markdown("## 📂 Chargement des données")

    dep_csv = st.file_uploader("Dépenses (CSV)", type="csv")
    bud_csv = st.file_uploader("Budget (CSV)", type="csv")

    if dep_csv:
        df_dep = pd.read_csv(dep_csv, sep=None, engine="python")
        st.session_state.df_depenses = normalize_depenses(df_dep)
        st.success("Dépenses chargées")

    if bud_csv:
        df_bud = pd.read_csv(bud_csv, sep=None, engine="python")
        st.session_state.df_budget = normalize_budget(df_bud)
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

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Dépenses brutes (€)", f"{dep_pos['montant_ttc'].sum():,.2f}".replace(",", " "))
    col2.metric("Avoirs (€)", f"{dep_neg['montant_ttc'].sum():,.2f}".replace(",", " "))
    col3.metric("Dépenses nettes (€)", f"{df_a['montant_ttc'].sum():,.2f}".replace(",", " "))
    col4.metric("Fournisseurs", df_a["fournisseur"].nunique())

    df_edit = st.data_editor(df_a, num_rows="dynamic", use_container_width=True)

    df_other = df_dep[df_dep["annee"] != annee]
    st.session_state.df_depenses = pd.concat([df_other, df_edit], ignore_index=True)

    st.download_button(
        "📥 Télécharger les dépenses",
        st.session_state.df_depenses.to_csv(index=False).encode("utf-8"),
        file_name="base_depenses_immeuble.csv",
        mime="text/csv",
    )

# ======================================================
# 💰 ONGLET 2 — BUDGET
# ======================================================
if page == "💰 Budget":

    annee_b = st.selectbox("Année budgétaire", sorted(df_budget["annee"].unique()))
    dfb = df_budget[df_budget["annee"] == annee_b].copy()

    col1, col2, col3 = st.columns(3)
    col1.metric("Budget total (€)", f"{dfb['budget'].sum():,.2f}".replace(",", " "))
    col2.metric("Comptes budgétés", len(dfb))
    col3.metric("Groupes", dfb["compte"].str[:2].nunique())

    df_edit = st.data_editor(dfb, num_rows="dynamic", use_container_width=True)

    df_other = df_budget[df_budget["annee"] != annee_b]
    st.session_state.df_budget = pd.concat([df_other, df_edit], ignore_index=True)

    st.download_button(
        "📥 Télécharger le budget",
        st.session_state.df_budget.to_csv(index=False).encode("utf-8"),
        file_name="budget_comptes_generaux.csv",
        mime="text/csv",
    )

# ======================================================
# 📊 ONGLET 3 — BUDGET VS RÉEL
# ======================================================
if page == "📊 Budget vs Réel – Pilotage":

    annee = st.selectbox("Année", sorted(df_dep["annee"].unique()))
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

    dep_pos = dep[dep["montant_ttc"] > 0]
    dep_neg = dep[dep["montant_ttc"] < 0]

    reel_dep = dep_pos.groupby("compte_budget")["montant_ttc"].sum().reset_index(name="depenses_brutes")
    avoirs = dep_neg.groupby("compte_budget")["montant_ttc"].sum().reset_index(name="avoirs")

    comp = bud.merge(reel_dep, left_on="compte", right_on="compte_budget", how="left")
    comp = comp.merge(avoirs, left_on="compte", right_on="compte_budget", how="left")

    comp["depenses_brutes"] = comp["depenses_brutes"].fillna(0)
    comp["avoirs"] = comp["avoirs"].fillna(0)
    comp["depenses_nettes"] = comp["depenses_brutes"] + comp["avoirs"]

    comp["ecart_eur"] = comp["depenses_nettes"] - comp["budget"]
    comp["ecart_pct"] = comp.apply(
        lambda r: (r["ecart_eur"] / r["budget"] * 100) if r["budget"] != 0 else 0,
        axis=1,
    )

    if only_over:
        comp = comp[comp["ecart_eur"] > 0]

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
