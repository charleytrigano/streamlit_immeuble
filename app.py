import streamlit as st
import pandas as pd
from supabase import create_client

# =========================================================
# CONFIG
# =========================================================
st.set_page_config(
    page_title="Pilotage des charges",
    layout="wide",
)

# =========================================================
# SUPABASE
# =========================================================
SUPABASE_URL = st.secrets["supabase_url"]
SUPABASE_KEY = st.secrets["supabase_anon_key"]

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

st.success("🚀 Connexion Supabase OK")

# =========================================================
# SIDEBAR – FILTRES GLOBAUX
# =========================================================
st.sidebar.header("🔎 Filtres globaux")

annee = st.sidebar.selectbox(
    "Année",
    options=[2024, 2025],
    index=1
)

# =========================================================
# TABS
# =========================================================
tab1, tab2 = st.tabs([
    "📊 Dépenses par groupe de charges",
    "📋 Détail des dépenses"
])

# =========================================================
# TAB 1 – DEPENSES PAR GROUPE
# =========================================================
with tab1:
    st.header("📊 Dépenses par groupe de charges")

    resp = supabase.table("v_depenses_par_groupe_charges").select("*").execute()
    df = pd.DataFrame(resp.data)

    if df.empty:
        st.warning("Aucune donnée")
    else:
        df = df[df["annee"] == annee]

        groupes = ["Tous"] + sorted(df["groupe_charges"].dropna().unique().tolist())
        groupe_sel = st.selectbox("Groupe de charges", groupes)

        if groupe_sel != "Tous":
            df = df[df["groupe_charges"] == groupe_sel]

        st.subheader("💰 Totaux")
        st.dataframe(
            df[["groupe_charges", "total_depenses"]]
            .sort_values("total_depenses", ascending=False),
            use_container_width=True
        )

        st.subheader("📈 Visualisation")
        st.bar_chart(
            df.set_index("groupe_charges")["total_depenses"]
        )

# =========================================================
# TAB 2 – DETAIL DES DEPENSES
# =========================================================
with tab2:
    st.header("📋 Détail des dépenses")

    resp = supabase.table("v_depenses_detail").select("*").execute()
    df = pd.DataFrame(resp.data)

    if df.empty:
        st.warning("Aucune dépense")
    else:
        df = df[df["annee"] == annee]

        col1, col2, col3 = st.columns(3)

        with col1:
            groupes = ["Tous"] + sorted(df["groupe_charges"].dropna().unique().tolist())
            groupe_sel = st.selectbox("Groupe de charges", groupes)

        with col2:
            comptes = ["Tous"] + sorted(df["compte"].dropna().unique().tolist())
            compte_sel = st.selectbox("Compte", comptes)

        with col3:
            postes = ["Tous"] + sorted(df["poste"].dropna().unique().tolist())
            poste_sel = st.selectbox("Poste", postes)

        if groupe_sel != "Tous":
            df = df[df["groupe_charges"] == groupe_sel]

        if compte_sel != "Tous":
            df = df[df["compte"] == compte_sel]

        if poste_sel != "Tous":
            df = df[df["poste"] == poste_sel]

        st.subheader("🧾 Liste des dépenses")

        st.dataframe(
            df.sort_values("date", ascending=False),
            use_container_width=True
        )

        st.subheader("⬇️ Export")
        st.download_button(
            "Télécharger en CSV",
            df.to_csv(index=False).encode("utf-8"),
            file_name=f"depenses_{annee}.csv",
            mime="text/csv"
        )