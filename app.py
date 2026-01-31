import streamlit as st
import pandas as pd
from supabase import create_client

# ======================================================
# CONFIG
# ======================================================
st.set_page_config(
    page_title="Pilotage des charges",
    layout="wide"
)

st.title("📊 Pilotage des charges – Dépenses")

# ======================================================
# SUPABASE (SANS IMPORT EXTERNE)
# ======================================================
supabase = create_client(
    st.secrets["SUPABASE_URL"],
    st.secrets["SUPABASE_SERVICE_ROLE_KEY"]
)

# ======================================================
# DATA
# ======================================================
@st.cache_data
def load_depenses():
    res = supabase.from_("v_depenses_enrichies").select("*").execute()
    return pd.DataFrame(res.data)

df = load_depenses()

if df.empty:
    st.warning("Aucune dépense.")
    st.stop()

# ======================================================
# FILTRES
# ======================================================
st.sidebar.header("🔎 Filtres")

annees = sorted(df["annee"].dropna().unique())
annee = st.sidebar.selectbox("Année", annees)

groupes_charges = ["Tous"] + sorted(df["groupe_charges"].dropna().unique())
groupe_charges = st.sidebar.selectbox("Groupe de charges", groupes_charges)

groupes_compte = ["Tous"] + sorted(df["groupe_compte"].dropna().unique())
groupe_compte = st.sidebar.selectbox("Groupe de compte", groupes_compte)

df_f = df[df["annee"] == annee]

if groupe_charges != "Tous":
    df_f = df_f[df_f["groupe_charges"] == groupe_charges]

if groupe_compte != "Tous":
    df_f = df_f[df_f["groupe_compte"] == groupe_compte]

# ======================================================
# TABS
# ======================================================
tab1, tab2 = st.tabs(["💰 Par groupe de charges", "📋 Détail des dépenses"])

with tab1:
    df_group = (
        df_f.groupby("groupe_charges", as_index=False)["montant_ttc"]
        .sum()
        .rename(columns={"montant_ttc": "total"})
        .sort_values("total", ascending=False)
    )
    st.dataframe(df_group, use_container_width=True)
    st.metric("Total", f"{df_group['total'].sum():,.2f} €")

with tab2:
    st.dataframe(
        df_f[
            [
                "date",
                "compte",
                "libelle_compte",
                "poste",
                "groupe_charges",
                "groupe_compte",
                "montant_ttc",
            ]
        ].sort_values("date"),
        use_container_width=True,
    )