import streamlit as st
import pandas as pd
from supabase import create_client

# =========================
# CONFIG
# =========================
st.set_page_config(
    page_title="Pilotage des charges",
    layout="wide"
)

# =========================
# SUPABASE
# =========================
@st.cache_resource
def get_supabase():
    return create_client(
        st.secrets["SUPABASE_URL"],
        st.secrets["SUPABASE_ANON_KEY"]
    )

supabase = get_supabase()

# =========================
# UTILS
# =========================
def safe_df(data):
    return pd.DataFrame(data) if data else pd.DataFrame()

def euro(x):
    try:
        return f"{x:,.2f} €".replace(",", " ").replace(".", ",")
    except Exception:
        return "0,00 €"

def load_table(name):
    try:
        return safe_df(
            supabase.table(name).select("*").execute().data
        )
    except Exception:
        return pd.DataFrame()

# =========================
# SIDEBAR – FILTRES
# =========================
st.sidebar.title("🔎 Filtres")

annee = st.sidebar.selectbox(
    "Année",
    ["Toutes", 2023, 2024, 2025, 2026],
    index=0
)

# =========================
# DATA LOAD
# =========================
df_dep = load_table("depenses")
df_bud = load_table("budgets")
df_rep = load_table("repartition_depenses")

# Filtre année (si colonne existe)
if annee != "Toutes" and "annee" in df_dep.columns:
    df_dep = df_dep[df_dep["annee"] == annee]

# =========================
# KPI GLOBAL
# =========================
st.title("📊 Pilotage des charges")

col1, col2, col3 = st.columns(3)

col1.metric(
    "💸 Total des dépenses",
    euro(df_dep["montant_ttc"].sum()) if "montant_ttc" in df_dep else "0,00 €"
)

col2.metric(
    "🧾 Nombre de dépenses",
    len(df_dep)
)

col3.metric(
    "💰 Budget total",
    euro(df_bud["montant"].sum()) if "montant" in df_bud else "0,00 €"
)

# =========================
# TABS
# =========================
tabs = st.tabs([
    "📄 État des dépenses",
    "💰 Budget",
    "📊 Budget vs Réel",
    "📈 Statistiques",
    "✅ Contrôle répartition"
])

# =========================
# 1. ÉTAT DES DÉPENSES
# =========================
with tabs[0]:
    st.subheader("📄 État des dépenses")

    cols = [
        c for c in [
            "date",
            "annee",
            "compte",
            "poste",
            "fournisseur",
            "montant_ttc",
            "commentaire"
        ] if c in df_dep.columns
    ]

    if cols:
        st.dataframe(
            df_dep[cols].sort_values(cols[0], ascending=False),
            use_container_width=True
        )
    else:
        st.info("Aucune colonne exploitable dans la table depenses")

# =========================
# 2. BUDGET
# =========================
with tabs[1]:
    st.subheader("💰 Budget")

    if df_bud.empty:
        st.info("Aucune donnée budget")
    else:
        st.dataframe(df_bud, use_container_width=True)

# =========================
# 3. BUDGET VS RÉEL
# =========================
with tabs[2]:
    st.subheader("📊 Budget vs Réel")

    if "montant_ttc" not in df_dep or "montant" not in df_bud:
        st.info("Données insuffisantes pour comparer")
    else:
        reel = df_dep["montant_ttc"].sum()
        budget = df_bud["montant"].sum()

        col1, col2, col3 = st.columns(3)
        col1.metric("Réel", euro(reel))
        col2.metric("Budget", euro(budget))
        col3.metric("Écart", euro(reel - budget))

# =========================
# 4. STATISTIQUES
# =========================
with tabs[3]:
    st.subheader("📈 Statistiques")

    if "poste" in df_dep and "montant_ttc" in df_dep:
        stats = (
            df_dep
            .groupby("poste", dropna=False)
            .agg(
                total=("montant_ttc", "sum"),
                nb=("montant_ttc", "count")
            )
            .reset_index()
        )
        st.dataframe(stats, use_container_width=True)
    else:
        st.info("Pas assez de données pour statistiques")

# =========================
# 5. CONTRÔLE RÉPARTITION
# =========================
with tabs[4]:
    st.subheader("✅ Contrôle de répartition")

    if df_rep.empty:
        st.info("Aucune répartition enregistrée")
    else:
        st.dataframe(df_rep, use_container_width=True)