import streamlit as st
import pandas as pd
from supabase import create_client

# =====================================================
# CONFIG
# =====================================================
BASE_TANTIEMES = 10_000

st.set_page_config(
    page_title="Pilotage des charges",
    layout="wide"
)

# =====================================================
# SUPABASE
# =====================================================
@st.cache_resource
def get_supabase():
    return create_client(
        st.secrets["SUPABASE_URL"],
        st.secrets["SUPABASE_ANON_KEY"]
    )

supabase = get_supabase()

# =====================================================
# UTILS
# =====================================================
def euro(x):
    return f"{x:,.2f} €".replace(",", " ").replace(".", ",")

def groupe_compte(compte: str) -> str:
    if compte in {"6211", "6213", "6222", "6223"}:
        return compte[:4]
    return compte[:3]

# =====================================================
# SIDEBAR
# =====================================================
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

annee = st.sidebar.selectbox(
    "Année",
    [2023, 2024, 2025, 2026],
    index=2
)

# =====================================================
# LOAD DATA (UNE FOIS)
# =====================================================
df_dep = pd.DataFrame(
    supabase.table("depenses")
    .select("id, annee, compte, montant_ttc")
    .eq("annee", annee)
    .execute()
    .data
)

df_budget = pd.DataFrame(
    supabase.table("budgets")
    .select("annee, groupe_compte, budget")
    .eq("annee", annee)
    .execute()
    .data
)

df_lots = pd.DataFrame(
    supabase.table("lots")
    .select("id, lot, tantiemes")
    .execute()
    .data
)

df_rep = pd.DataFrame(
    supabase.table("repartition_depenses")
    .select("depense_id, lot_id, quote_part")
    .execute()
    .data
)

# =====================================================
# 📄 ÉTAT DES DÉPENSES
# =====================================================
if page == "📄 État des dépenses":
    st.title("📄 État des dépenses")

    if df_dep.empty:
        st.warning("Aucune dépense")
    else:
        st.metric("Total dépenses", euro(df_dep["montant_ttc"].sum()))
        st.dataframe(df_dep, use_container_width=True)

# =====================================================
# 💰 BUDGET
# =====================================================
if page == "💰 Budget":
    st.title("💰 Budget")

    if df_budget.empty:
        st.warning("Aucun budget")
    else:
        st.metric("Budget total", euro(df_budget["budget"].sum()))
        st.dataframe(df_budget, use_container_width=True)

# =====================================================
# 📊 BUDGET VS RÉEL
# =====================================================
if page == "📊 Budget vs Réel":
    st.title("📊 Budget vs Réel")

    if df_dep.empty or df_budget.empty:
        st.warning("Données insuffisantes")
    else:
        df_dep["groupe_compte"] = df_dep["compte"].astype(str).apply(groupe_compte)

        reel = (
            df_dep
            .groupby("groupe_compte", as_index=False)
            .agg(reel=("montant_ttc", "sum"))
        )

        comp = (
            df_budget
            .groupby("groupe_compte", as_index=False)
            .agg(budget=("budget", "sum"))
            .merge(reel, on="groupe_compte", how="left")
            .fillna(0)
        )

        comp["ecart"] = comp["reel"] - comp["budget"]
        comp["ecart_pct"] = comp.apply(
            lambda r: (r["ecart"] / r["budget"] * 100) if r["budget"] != 0 else 0,
            axis=1
        )

        c1, c2, c3 = st.columns(3)
        c1.metric("Budget", euro(comp["budget"].sum()))
        c2.metric("Réel", euro(comp["reel"].sum()))
        c3.metric("Écart", euro(comp["ecart"].sum()))

        st.dataframe(comp, use_container_width=True)

# =====================================================
# 📈 STATISTIQUES
# =====================================================
if page == "📈 Statistiques":
    st.title("📈 Statistiques")

    if df_dep.empty:
        st.warning("Aucune donnée")
    else:
        by_compte = (
            df_dep
            .groupby("compte", as_index=False)
            .agg(total=("montant_ttc", "sum"))
            .sort_values("total", ascending=False)
        )
        st.dataframe(by_compte, use_container_width=True)

# =====================================================
# 🚨 CONTRÔLE DE RÉPARTITION
# =====================================================
if page == "🚨 Contrôle de répartition":
    st.title("🚨 Contrôle de répartition")

    if df_dep.empty or df_rep.empty:
        st.warning("Données insuffisantes")
    else:
        ctrl = (
            df_rep
            .merge(df_dep, left_on="depense_id", right_on="id", how="left")
        )

        ctrl["montant_reparti"] = ctrl["montant_ttc"] * ctrl["quote_part"] / BASE_TANTIEMES

        check = (
            ctrl
            .groupby("depense_id", as_index=False)
            .agg(
                montant=("montant_ttc", "first"),
                reparti=("montant_reparti", "sum")
            )
        )

        check["ecart"] = check["montant"] - check["reparti"]

        anomalies = check[check["ecart"].abs() > 0.01]

        if anomalies.empty:
            st.success("Toutes les dépenses sont correctement réparties")
        else:
            st.error(f"{len(anomalies)} anomalie(s)")
            st.dataframe(anomalies, use_container_width=True)