import streamlit as st
import pandas as pd
from supabase_client import supabase

# ======================================================
# CONFIG
# ======================================================
st.set_page_config(
    page_title="Pilotage des charges",
    layout="wide"
)

st.title("📊 Pilotage des charges – Dépenses")

# ======================================================
# CHARGEMENT DES DONNÉES
# ======================================================
@st.cache_data
def load_depenses():
    res = (
        supabase
        .from_("v_depenses_enrichies")
        .select("*")
        .execute()
    )
    return pd.DataFrame(res.data)

df = load_depenses()

if df.empty:
    st.warning("Aucune dépense disponible.")
    st.stop()

# ======================================================
# FILTRES GLOBAUX
# ======================================================
st.sidebar.header("🔎 Filtres")

annees = sorted(df["annee"].dropna().unique().tolist())
annee_sel = st.sidebar.selectbox("Année", annees)

groupes_charges = ["Tous"] + sorted(df["groupe_charges"].dropna().unique().tolist())
groupe_charges_sel = st.sidebar.selectbox("Groupe de charges", groupes_charges)

groupes_compte = ["Tous"] + sorted(df["groupe_compte"].dropna().unique().tolist())
groupe_compte_sel = st.sidebar.selectbox("Groupe de compte", groupes_compte)

# ======================================================
# APPLICATION DES FILTRES
# ======================================================
df_filtree = df[df["annee"] == annee_sel]

if groupe_charges_sel != "Tous":
    df_filtree = df_filtree[df_filtree["groupe_charges"] == groupe_charges_sel]

if groupe_compte_sel != "Tous":
    df_filtree = df_filtree[df_filtree["groupe_compte"] == groupe_compte_sel]

# ======================================================
# ONGLET
# ======================================================
tab1, tab2 = st.tabs([
    "💰 Dépenses par groupe de charges",
    "📋 Détail des dépenses"
])

# ======================================================
# ONGLET 1 — AGRÉGATION
# ======================================================
with tab1:
    st.subheader("💰 Dépenses par groupe de charges")

    df_group = (
        df_filtree
        .groupby("groupe_charges", as_index=False)["montant_ttc"]
        .sum()
        .rename(columns={"montant_ttc": "total_depenses"})
        .sort_values("total_depenses", ascending=False)
    )

    st.dataframe(
        df_group,
        use_container_width=True
    )

    st.metric(
        "Total général",
        f"{df_group['total_depenses'].sum():,.2f} €"
    )

# ======================================================
# ONGLET 2 — DÉTAIL
# ======================================================
with tab2:
    st.subheader("📋 Détail des dépenses")

    colonnes = [
        "date",
        "compte",
        "libelle_compte",
        "poste",
        "groupe_charges",
        "groupe_compte",
        "montant_ttc"
    ]

    st.dataframe(
        df_filtree[colonnes].sort_values("date"),
        use_container_width=True
    )