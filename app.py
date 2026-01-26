import streamlit as st
import pandas as pd
from supabase import create_client
import os

# =========================
# CONFIG
# =========================
st.set_page_config(
    page_title="Pilotage des charges de l’immeuble",
    layout="wide"
)

SUPABASE_URL = os.environ["SUPABASE_URL"]
SUPABASE_KEY = os.environ["SUPABASE_KEY"]
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# =========================
# UTILS
# =========================
def load_table(table, filters=None):
    q = supabase.table(table).select("*")
    if filters:
        for k, v in filters.items():
            q = q.eq(k, v)
    return pd.DataFrame(q.execute().data)

# =========================
# SIDEBAR – FILTRES
# =========================
st.sidebar.header("Filtres")

annees = (
    supabase.table("budgets")
    .select("annee")
    .execute()
    .data
)
annees = sorted({a["annee"] for a in annees})

annee = st.sidebar.selectbox("Année", annees)

# =========================
# TITRE
# =========================
st.title("🏢 Pilotage des charges de l’immeuble")

# =========================
# 1️⃣ ÉTAT DES DÉPENSES
# =========================
st.subheader("📋 État des dépenses")

df_depenses = load_table("depenses", {"annee": annee})

st.metric(
    "Total dépenses enregistrées",
    f"{df_depenses['montant_ttc'].sum():,.2f} €"
)

st.dataframe(
    df_depenses.sort_values("date", ascending=False),
    use_container_width=True
)

# =========================
# 2️⃣ BUDGET
# =========================
st.subheader("💰 Budget")

df_budget = load_table("budgets", {"annee": annee})

budget_total = df_budget["budget"].sum()

st.metric(
    "Budget total voté",
    f"{budget_total:,.2f} €"
)

st.dataframe(df_budget, use_container_width=True)

# =========================
# 3️⃣ BUDGET VS RÉEL
# =========================
st.subheader("📊 Budget vs Réel")

df_bvr = load_table("v_budget_vs_reel", {"annee": annee})

col1, col2, col3 = st.columns(3)

with col1:
    st.metric(
        "Appels de fonds",
        f"{df_bvr['appel_fonds'].sum():,.2f} €"
    )

with col2:
    st.metric(
        "Charges réelles",
        f"{df_bvr['charges_reelles'].sum():,.2f} €"
    )

with col3:
    st.metric(
        "Régularisation globale",
        f"{df_bvr['regularisation'].sum():,.2f} €"
    )

st.dataframe(
    df_bvr.sort_values("lot"),
    use_container_width=True
)

# =========================
# 4️⃣ STATISTIQUES
# =========================
st.subheader("📈 Statistiques")

stats = pd.DataFrame({
    "Indicateur": [
        "Nombre de dépenses",
        "Charge moyenne par lot",
        "Lot le plus chargé",
        "Lot le moins chargé",
    ],
    "Valeur": [
        len(df_depenses),
        round(df_bvr["charges_reelles"].mean(), 2),
        df_bvr.loc[df_bvr["charges_reelles"].idxmax(), "lot"],
        df_bvr.loc[df_bvr["charges_reelles"].idxmin(), "lot"],
    ]
})

st.dataframe(stats, use_container_width=True)

# =========================
# 5️⃣ CONTRÔLE DES RÉPARTITIONS
# =========================
st.subheader("🛑 Contrôle des répartitions")

controle = (
    supabase
    .rpc(
        "controle_repartition_depenses",
        {"p_annee": annee}
    )
    .execute()
    .data
)

df_controle = pd.DataFrame(controle)

if len(df_controle) == 0:
    st.success("✅ Toutes les dépenses sont réparties à 100 %")
else:
    st.error("❌ Certaines dépenses ne sont PAS réparties à 100 %")
    st.dataframe(df_controle, use_container_width=True)