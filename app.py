import streamlit as st
import pandas as pd
from supabase import create_client

# =========================
# CONFIG STREAMLIT
# =========================
st.set_page_config(
    page_title="Pilotage des charges de l’immeuble",
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

def load_view(view_name, filters=None):
    q = supabase.table(view_name).select("*")
    if filters:
        for k, v in filters.items():
            q = q.eq(k, v)
    return pd.DataFrame(q.execute().data)

# =========================
# SIDEBAR – FILTRES
# =========================
st.sidebar.title("Filtres")

annee = st.sidebar.selectbox(
    "Année",
    [2023, 2024, 2025, 2026],
    index=2
)

# =========================
# TITRE
# =========================
st.title("🏢 Pilotage des charges de l’immeuble")

# ======================================================
# 1️⃣ ÉTAT DES DÉPENSES
# ======================================================
st.header("📄 État des dépenses")

df_dep = load_view("v_etat_depenses", {"annee": annee})

if df_dep.empty:
    st.info("Aucune dépense pour cette année.")
else:
    st.dataframe(df_dep, use_container_width=True)

# ======================================================
# 2️⃣ CONTRÔLE DE RÉPARTITION
# ======================================================
st.header("🚨 Contrôle de répartition")

df_ctrl = load_view("v_controle_repartition")

if df_ctrl.empty:
    st.success("✅ Toutes les dépenses sont réparties à 100 %")
else:
    st.error("❌ Certaines dépenses ne sont PAS réparties à 100 %")
    st.dataframe(df_ctrl, use_container_width=True)

# ======================================================
# 3️⃣ BUDGET
# ======================================================
st.header("💰 Budget")

df_budget = load_view("v_budget", {"annee": annee})

if df_budget.empty:
    st.warning("Aucun budget défini pour cette année.")
    budget_total = 0
else:
    budget_total = df_budget.iloc[0]["budget_total"]
    st.metric(
        "Budget total",
        f"{budget_total:,.2f} €".replace(",", " ").replace(".", ",")
    )

# ======================================================
# 4️⃣ BUDGET VS RÉEL
# ======================================================
st.header("📊 Budget vs Réel")

df_bvr = load_view("v_budget_vs_reel", {"annee": annee})

if not df_bvr.empty:
    charges_reelles = df_bvr.iloc[0]["charges_reelles"]
    charges_reparties = df_bvr.iloc[0]["charges_reparties"]
else:
    charges_reelles = 0
    charges_reparties = 0

col1, col2, col3 = st.columns(3)

col1.metric(
    "Charges réelles",
    f"{charges_reelles:,.2f} €".replace(",", " ").replace(".", ",")
)

col2.metric(
    "Charges réparties",
    f"{charges_reparties:,.2f} €".replace(",", " ").replace(".", ",")
)

col3.metric(
    "Écart budget / réel",
    f"{(charges_reelles - budget_total):,.2f} €".replace(",", " ").replace(".", ",")
)

# ======================================================
# 5️⃣ STATISTIQUES
# ======================================================
st.header("📈 Statistiques")

if not df_dep.empty:
    stats = pd.DataFrame({
        "Indicateur": [
            "Nombre de dépenses",
            "Montant total facturé",
            "Montant réparti"
        ],
        "Valeur": [
            len(df_dep),
            df_dep["montant_ttc"].sum(),
            (df_dep["montant_ttc"] * df_dep["total_quote_part"]).sum()
        ]
    })

    stats["Valeur"] = stats["Valeur"].apply(
        lambda x: f"{x:,.2f} €".replace(",", " ").replace(".", ",")
        if isinstance(x, float) else x
    )

    st.dataframe(stats, use_container_width=True)

# =========================
# FIN
# =========================
st.caption("Données issues exclusivement de Supabase – aucune correction silencieuse.")