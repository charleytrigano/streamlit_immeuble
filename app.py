import streamlit as st
import pandas as pd
from supabase import create_client

# =========================
# CONFIG
# =========================
st.set_page_config(
    page_title="🏢 Pilotage des charges",
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
# OUTILS
# =========================
def load_view(view_name, filters=None):
    q = supabase.table(view_name).select("*")
    if filters:
        for k, v in filters.items():
            q = q.eq(k, v)
    res = q.execute()
    return pd.DataFrame(res.data)

def euro(x):
    return f"{x:,.2f} €".replace(",", " ").replace(".", ",")

# =========================
# SIDEBAR
# =========================
st.sidebar.title("Navigation")

page = st.sidebar.radio(
    "Aller à",
    [
        "📄 État des dépenses",
        "💰 Budget",
        "📊 Budget vs Réel",
        "📈 Statistiques",
        "🚨 Contrôle de répartition"
    ]
)

# =========================
# FILTRE ANNÉE GLOBAL
# =========================
annee = st.sidebar.selectbox(
    "Année",
    [2023, 2024, 2025, 2026],
    index=2
)

# =========================
# 📄 ÉTAT DES DÉPENSES
# =========================
if page == "📄 État des dépenses":
    st.title("📄 État des dépenses")

    df = load_view("v_etat_depenses", {"annee": annee})

    if df.empty:
        st.warning("Aucune dépense")
        st.stop()

    col1, col2, col3 = st.columns(3)
    col1.metric("Total dépenses", euro(df["montant_ttc"].sum()))
    col2.metric("Nombre de lignes", len(df))
    col3.metric("Dépense moyenne", euro(df["montant_ttc"].mean()))

    st.dataframe(df, use_container_width=True)

# =========================
# 💰 BUDGET
# =========================
elif page == "💰 Budget":
    st.title("💰 Budget")

    df = load_view("budgets", {"annee": annee})

    if df.empty:
        st.warning("Aucun budget")
        st.stop()

    st.metric("Budget total", euro(df["montant"].sum()))
    st.dataframe(df, use_container_width=True)

# =========================
# 📊 BUDGET VS RÉEL
# =========================
elif page == "📊 Budget vs Réel":
    st.title("📊 Budget vs Réel")

    df = load_view("v_budget_vs_reel", {"annee": annee})

    if df.empty:
        st.warning("Aucune donnée")
        st.stop()

    col1, col2, col3 = st.columns(3)
    col1.metric("Budget", euro(df["budget"].sum()))
    col2.metric("Réel", euro(df["reel"].sum()))
    col3.metric("Écart", euro(df["ecart"].sum()))

    st.dataframe(df, use_container_width=True)

# =========================
# 📈 STATISTIQUES
# =========================
elif page == "📈 Statistiques":
    st.title("📈 Statistiques")

    df = load_view("v_statistiques", {"annee": annee})

    if df.empty:
        st.warning("Aucune statistique")
        st.stop()

    lot = st.selectbox("Lot", ["Tous"] + sorted(df["lot"].astype(str).unique()))
    compte = st.selectbox("Compte", ["Tous"] + sorted(df["compte"].astype(str).unique()))

    if lot != "Tous":
        df = df[df["lot"].astype(str) == lot]

    if compte != "Tous":
        df = df[df["compte"].astype(str) == compte]

    st.metric("Charges réelles", euro(df["charges_reelles"].sum()))
    st.dataframe(df, use_container_width=True)

# =========================
# 🚨 CONTRÔLE RÉPARTITION
# =========================
elif page == "🚨 Contrôle de répartition":
    st.title("🚨 Contrôle de répartition")

    df = load_view("v_controle_repartition")

    if df.empty:
        st.warning("Aucune anomalie")
        st.stop()

    anomalies = df[df["ecart"].abs() > 0.01]

    col1, col2 = st.columns(2)
    col1.metric("Dépenses", euro(df["montant_depense"].sum()))
    col2.metric("Écart total", euro(df["ecart"].sum()))

    if anomalies.empty:
        st.success("✅ Toutes les dépenses sont correctement réparties")
    else:
        st.error(f"❌ {len(anomalies)} anomalies détectées")
        st.dataframe(anomalies, use_container_width=True)