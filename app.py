import streamlit as st
import pandas as pd
from supabase import create_client

# =========================
# CONFIG
# =========================
st.set_page_config(page_title="Pilotage des charges", layout="wide")

SUPABASE_URL = st.secrets["SUPABASE_URL"]
SUPABASE_KEY = st.secrets["SUPABASE_ANON_KEY"]
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# =========================
# LOADERS
# =========================
@st.cache_data
def load_depenses():
    return pd.DataFrame(
        supabase.table("depenses").select("*").execute().data
    )

@st.cache_data
def load_plan():
    return pd.DataFrame(
        supabase.table("plan_comptable").select("*").execute().data
    )

@st.cache_data
def load_budgets():
    return pd.DataFrame(
        supabase.table("budgets").select("*").execute().data
    )

# =========================
# DATA
# =========================
df_dep = load_depenses()
df_plan = load_plan()
df_bud = load_budgets()

# =========================
# SIDEBAR FILTERS
# =========================
st.sidebar.header("🔎 Filtres")

annees = sorted(df_dep["annee"].unique())
annee = st.sidebar.selectbox("Année", annees)

df_dep_y = df_dep[df_dep["annee"] == annee]
df_bud_y = df_bud[df_bud["annee"] == annee]

# =========================
# KPIs
# =========================
dep_total = df_dep_y["montant_ttc"].sum()
bud_total = df_bud_y["montant"].sum() if not df_bud_y.empty else 0
ecart = bud_total - dep_total

c1, c2, c3 = st.columns(3)
c1.metric("💸 Dépenses réelles", f"{dep_total:,.2f} €")
c2.metric("💰 Budget", f"{bud_total:,.2f} €")
c3.metric("📉 Écart", f"{ecart:,.2f} €")

# =========================
# TABS
# =========================
tab1, tab2, tab3 = st.tabs([
    "📄 État des dépenses",
    "📘 Plan comptable",
    "💰 Budgets"
])

# =========================
# TAB 1 – DÉPENSES
# =========================
with tab1:
    st.subheader("État des dépenses")
    st.dataframe(df_dep_y, use_container_width=True)

# =========================
# TAB 2 – PLAN COMPTABLE
# =========================
with tab2:
    st.subheader("Plan comptable")

    st.dataframe(df_plan, use_container_width=True)

    st.markdown("### ➕ Ajouter / modifier un compte")
    with st.form("plan_form"):
        compte_8 = st.text_input("Compte (8 chiffres)")
        libelle = st.text_input("Libellé")
        groupe = st.text_input("Groupe (3 chiffres)")
        lib_groupe = st.text_input("Libellé groupe")

        submit = st.form_submit_button("Enregistrer")

        if submit:
            supabase.table("plan_comptable").upsert({
                "compte_8": compte_8,
                "libelle": libelle,
                "groupe_compte": groupe,
                "libelle_groupe": lib_groupe
            }).execute()
            st.cache_data.clear()
            st.success("Compte enregistré")

# =========================
# TAB 3 – BUDGETS
# =========================
with tab3:
    st.subheader("Budgets")

    st.dataframe(df_bud_y, use_container_width=True)

    st.markdown("### ➕ Ajouter / modifier un budget")
    with st.form("budget_form"):
        an = st.number_input("Année", value=int(annee))
        compte = st.selectbox("Compte", sorted(df_plan["compte_8"].unique()))
        montant = st.number_input("Montant", min_value=0.0)

        submit = st.form_submit_button("Enregistrer")

        if submit:
            supabase.table("budgets").upsert({
                "annee": an,
                "compte_8": compte,
                "montant": montant
            }).execute()
            st.cache_data.clear()
            st.success("Budget enregistré")
