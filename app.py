import streamlit as st
import pandas as pd
from supabase import create_client

# =====================
# CONFIG
# =====================
st.set_page_config(
    page_title="Pilotage des charges",
    layout="wide"
)

def euro(v):
    return f"{v:,.2f} €".replace(",", " ").replace(".", ",")

# =====================
# SUPABASE
# =====================
@st.cache_resource
def get_supabase():
    return create_client(
        st.secrets["SUPABASE_URL"],
        st.secrets["SUPABASE_ANON_KEY"]
    )

supabase = get_supabase()

# =====================
# SIDEBAR
# =====================
st.sidebar.title("🔎 Filtres")

annee = st.sidebar.selectbox(
    "Année",
    [2023, 2024, 2025, 2026],
    index=2
)

onglet = st.sidebar.radio(
    "Navigation",
    [
        "📄 État des dépenses",
        "💰 Budget",
        "📊 Budget vs Réel",
        "📈 Statistiques",
        "✅ Contrôle répartition"
    ]
)

# =====================
# ÉTAT DES DÉPENSES
# =====================
if onglet == "📄 État des dépenses":
    df = pd.DataFrame(
        supabase.table("v_etat_depenses")
        .select("*")
        .eq("annee", annee)
        .execute()
        .data
    )

    st.title("📄 État des dépenses")

    col1, col2, col3 = st.columns(3)
    col1.metric("Total dépenses", euro(df["montant_ttc"].sum()))
    col2.metric("Nombre de lignes", len(df))
    col3.metric("Dépense moyenne", euro(df["montant_ttc"].mean()))

    st.dataframe(
        df[[
            "date",
            "compte",
            "poste",
            "fournisseur",
            "montant_ttc",
            "commentaire",
            "facture_path"
        ]],
        use_container_width=True
    )

# =====================
# BUDGET
# =====================
elif onglet == "💰 Budget":
    df = pd.DataFrame(
        supabase.table("budgets")
        .select("*")
        .eq("annee", annee)
        .execute()
        .data
    )

    st.title("💰 Budget")

    st.metric("Budget total", euro(df["montant"].sum()))

    st.dataframe(df, use_container_width=True)

# =====================
# BUDGET VS RÉEL
# =====================
elif onglet == "📊 Budget vs Réel":
    df = pd.DataFrame(
        supabase.table("v_budget_vs_reel")
        .select("*")
        .eq("annee", annee)
        .execute()
        .data
    )

    st.title("📊 Budget vs Réel")

    col1, col2, col3 = st.columns(3)
    col1.metric("Budget", euro(df["budget"].sum()))
    col2.metric("Réel", euro(df["reel"].sum()))
    col3.metric("Écart", euro(df["ecart"].sum()))

    st.dataframe(df, use_container_width=True)

# =====================
# STATISTIQUES
# =====================
elif onglet == "📈 Statistiques":
    df = pd.DataFrame(
        supabase.table("v_charges_reelles")
        .select("*")
        .eq("annee", annee)
        .execute()
        .data
    )

    st.title("📈 Statistiques")

    st.dataframe(
        df.groupby("poste", as_index=False)
        .agg(total=("charge_reelle", "sum"))
        .sort_values("total", ascending=False),
        use_container_width=True
    )

# =====================
# CONTRÔLE RÉPARTITION
# =====================
elif onglet == "✅ Contrôle répartition":
    df = pd.DataFrame(
        supabase.table("v_controle_repartition")
        .select("*")
        .eq("annee", annee)
        .execute()
        .data
    )

    st.title("✅ Contrôle de répartition")

    erreurs = df[df["statut"] != "OK"]

    if erreurs.empty:
        st.success("Toutes les dépenses sont correctement réparties")
    else:
        st.error("Dépenses mal réparties détectées")
        st.dataframe(erreurs, use_container_width=True)