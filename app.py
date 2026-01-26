import os
import pandas as pd
import streamlit as st
from supabase import create_client

# ======================================================
# CONFIG STREAMLIT
# ======================================================
st.set_page_config(
    page_title="Pilotage des charges de l’immeuble",
    layout="wide"
)

st.title("🏢 Pilotage des charges de l’immeuble")

# ======================================================
# SUPABASE
# ======================================================
@st.cache_resource
def get_supabase():
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_ANON_KEY"]
    return create_client(url, key)

supabase = get_supabase()

# ======================================================
# DATA LOADERS (SAFE)
# ======================================================
def load_view(view_name, filters=None):
    try:
        q = supabase.table(view_name).select("*")

        if filters:
            for k, v in filters.items():
                q = q.eq(k, v)

        res = q.execute()

        if not res.data:
            return pd.DataFrame()

        return pd.DataFrame(res.data)

    except Exception as e:
        st.error(f"Erreur Supabase sur `{view_name}`")
        st.exception(e)
        return pd.DataFrame()

# ======================================================
# SIDEBAR
# ======================================================
st.sidebar.header("Filtres")

annees = load_view("v_etat_depenses")["annee"].dropna().unique()
annees = sorted(annees) if len(annees) else []

annee = st.sidebar.selectbox(
    "Année",
    annees,
    index=len(annees) - 1 if annees else 0
)

# ======================================================
# ONGLET : ÉTAT DES DÉPENSES
# ======================================================
st.header("📄 État des dépenses")

df_depenses = load_view("v_etat_depenses", {"annee": annee})

if df_depenses.empty:
    st.info("Aucune dépense pour cette année.")
else:
    st.dataframe(
        df_depenses,
        use_container_width=True,
        hide_index=True
    )

# ======================================================
# ONGLET : CONTRÔLE DE RÉPARTITION
# ======================================================
st.header("🚨 Contrôle de répartition")

df_ctrl = load_view("v_controle_repartition", {"annee": annee})

if df_ctrl.empty:
    st.success("✅ Toutes les dépenses sont réparties à 100 %")
else:
    st.error("❌ Certaines dépenses ne sont PAS réparties à 100 %")
    st.dataframe(
        df_ctrl,
        use_container_width=True,
        hide_index=True
    )

# ======================================================
# ONGLET : BUDGET
# ======================================================
st.header("💰 Budget")

df_budget = load_view("v_budget_total", {"annee": annee})

budget_total = (
    df_budget["budget_total"].sum()
    if not df_budget.empty
    else 0
)

st.metric(
    label="Budget total",
    value=f"{budget_total:,.2f} €".replace(",", " ")
)

# ======================================================
# ONGLET : BUDGET VS RÉEL
# ======================================================
st.header("📊 Budget vs Réel")

df_bvr = load_view("v_budget_vs_reel", {"annee": annee})

if df_bvr.empty:
    st.info("Aucune donnée budget / réel.")
else:
    charges_reelles = df_bvr["charges_reelles"].sum()
    charges_reparties = df_bvr["charges_reparties"].sum()
    ecart = charges_reelles - budget_total

    col1, col2, col3 = st.columns(3)

    col1.metric(
        "Charges réelles",
        f"{charges_reelles:,.2f} €".replace(",", " ")
    )

    col2.metric(
        "Charges réparties",
        f"{charges_reparties:,.2f} €".replace(",", " ")
    )

    col3.metric(
        "Écart budget / réel",
        f"{ecart:,.2f} €".replace(",", " ")
    )

# ======================================================
# ONGLET : STATISTIQUES
# ======================================================
st.header("📈 Statistiques")

if df_depenses.empty:
    st.info("Pas de statistiques disponibles.")
else:
    stats = pd.DataFrame(
        {
            "Indicateur": [
                "Nombre de dépenses",
                "Montant total facturé",
                "Montant réparti",
            ],
            "Valeur": [
                len(df_depenses),
                df_depenses["montant_ttc"].sum(),
                df_depenses["montant_reparti"].sum()
                if "montant_reparti" in df_depenses.columns
                else 0,
            ],
        }
    )

    st.dataframe(stats, hide_index=True)

st.caption(
    "Données issues exclusivement de Supabase — aucune correction silencieuse."
)