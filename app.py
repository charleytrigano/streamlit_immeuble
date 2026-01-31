import streamlit as st
import pandas as pd
from supabase import create_client

# --------------------------------------------------
# CONFIG
# --------------------------------------------------
st.set_page_config(
    page_title="Pilotage des charges",
    layout="wide"
)

# --------------------------------------------------
# SUPABASE
# --------------------------------------------------
supabase = create_client(
    st.secrets["SUPABASE_URL"],
    st.secrets["SUPABASE_ANON_KEY"]
)

# --------------------------------------------------
# SIDEBAR – FILTRES GLOBAUX
# --------------------------------------------------
st.sidebar.title("Filtres globaux")

# Années disponibles
years_resp = supabase.table("v_depenses_detail") \
    .select("annee") \
    .execute()

years = sorted({row["annee"] for row in years_resp.data})
annee = st.sidebar.selectbox("Année", years, index=len(years) - 1)

# Groupes de charges disponibles
groups_resp = supabase.table("v_depenses_detail") \
    .select("groupe_charges") \
    .eq("annee", annee) \
    .execute()

groupes = sorted({row["groupe_charges"] for row in groups_resp.data if row["groupe_charges"]})
groupe_selected = st.sidebar.multiselect(
    "Groupe de charges",
    groupes,
    default=groupes
)

# --------------------------------------------------
# ONGLET PRINCIPAL
# --------------------------------------------------
st.title("📊 Pilotage des charges")

tab1, tab2 = st.tabs([
    "📈 Dépenses par groupe de charges",
    "📋 Détail des dépenses"
])

# --------------------------------------------------
# ONGLET 1 – SYNTHESE
# --------------------------------------------------
with tab1:
    st.subheader("Dépenses par groupe de charges")

    query = supabase.table("v_depenses_par_groupe_charges") \
        .select("*") \
        .eq("annee", annee)

    if groupe_selected:
        query = query.in_("groupe_charges", groupe_selected)

    data = query.execute().data
    df = pd.DataFrame(data)

    if df.empty:
        st.warning("Aucune donnée")
    else:
        df = df.sort_values("total_depenses", ascending=False)

        st.dataframe(
            df,
            use_container_width=True
        )

        st.bar_chart(
            df.set_index("groupe_charges")["total_depenses"]
        )

# --------------------------------------------------
# ONGLET 2 – DETAIL
# --------------------------------------------------
with tab2:
    st.subheader("Détail des dépenses")

    query = supabase.table("v_depenses_detail") \
        .select("*") \
        .eq("annee", annee)

    if groupe_selected:
        query = query.in_("groupe_charges", groupe_selected)

    data = query.execute().data
    df = pd.DataFrame(data)

    if df.empty:
        st.warning("Aucune dépense")
    else:
        df = df.sort_values("date", ascending=False)

        st.dataframe(
            df,
            use_container_width=True,
            hide_index=True
        )