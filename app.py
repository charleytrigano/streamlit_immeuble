import streamlit as st
import pandas as pd
from supabase import create_client

# =========================
# CONFIG
# =========================
BASE_TANTIEMES = 10_000

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
# HELPERS
# =========================
def euro(x):
    return f"{x:,.2f} €".replace(",", " ").replace(".", ",")

def groupe_compte(compte: str) -> str:
    compte = str(compte)
    if compte in {"6211", "6213", "6222", "6223"}:
        return compte[:4]
    return compte[:3]

# =========================
# LOADERS
# =========================
@st.cache_data
def load_depenses():
    df = pd.DataFrame(
        supabase.table("depenses").select("*").execute().data
    )
    df["date"] = pd.to_datetime(df["date"])
    df["annee"] = df["date"].dt.year
    df["groupe_compte"] = df["compte"].apply(groupe_compte)
    return df

@st.cache_data
def load_budgets():
    return pd.DataFrame(
        supabase.table("budgets").select("*").execute().data
    )

@st.cache_data
def load_lots():
    return pd.DataFrame(
        supabase.table("lots").select("*").execute().data
    )

@st.cache_data
def load_repartition():
    return pd.DataFrame(
        supabase.table("repartition_depenses").select("*").execute().data
    )

# =========================
# DATA
# =========================
df_dep = load_depenses()
df_bud = load_budgets()
df_lots = load_lots()
df_rep = load_repartition()

# =========================
# SIDEBAR – FILTRES
# =========================
st.sidebar.title("🔎 Filtres")

annee = st.sidebar.selectbox(
    "Année",
    sorted(df_dep["annee"].unique())
)

df_f = df_dep[df_dep["annee"] == annee]

compte = st.sidebar.selectbox(
    "Compte",
    ["Tous"] + sorted(df_f["compte"].dropna().unique())
)

fournisseur = st.sidebar.selectbox(
    "Fournisseur",
    ["Tous"] + sorted(df_f["fournisseur"].dropna().unique())
)

poste = st.sidebar.selectbox(
    "Poste",
    ["Tous"] + sorted(df_f["poste"].dropna().unique())
)

if compte != "Tous":
    df_f = df_f[df_f["compte"] == compte]

if fournisseur != "Tous":
    df_f = df_f[df_f["fournisseur"] == fournisseur]

if poste != "Tous":
    df_f = df_f[df_f["poste"] == poste]

# =========================
# TABS
# =========================
tab_dep, tab_bud, tab_bvr, tab_stats, tab_ctrl = st.tabs([
    "📄 État des dépenses",
    "💰 Budget",
    "📊 Budget vs Réel",
    "📈 Statistiques",
    "✅ Contrôle répartition"
])

# =========================
# 📄 ÉTAT DES DÉPENSES
# =========================
with tab_dep:
    st.subheader("📄 État des dépenses")

    c1, c2, c3 = st.columns(3)
    c1.metric("Total dépenses", euro(df_f["montant_ttc"].sum()))
    c2.metric("Nombre de lignes", len(df_f))
    c3.metric("Dépense moyenne", euro(df_f["montant_ttc"].mean() if len(df_f) else 0))

    df_view = df_f.copy()
    df_view["Facture"] = df_view["facture_url"].apply(
        lambda x: f"[📎 Ouvrir]({x})" if pd.notna(x) else ""
    )

    st.dataframe(
        df_view[[
            "date",
            "compte",
            "poste",
            "fournisseur",
            "montant_ttc",
            "Facture",
            "commentaire"
        ]],
        use_container_width=True
    )

# =========================
# 💰 BUDGET
# =========================
with tab_bud:
    st.subheader("💰 Budget")

    df_bud_y = df_bud[df_bud["annee"] == annee]

    c1, c2 = st.columns(2)
    c1.metric("Budget total", euro(df_bud_y["budget"].sum()))
    c2.metric("Nombre de lignes", len(df_bud_y))

    st.dataframe(
        df_bud_y[["compte", "groupe_compte", "budget"]],
        use_container_width=True
    )

# =========================
# 📊 BUDGET VS RÉEL
# =========================
with tab_bvr:
    st.subheader("📊 Budget vs Réel")

    reel = (
        df_f
        .groupby("groupe_compte", as_index=False)
        .agg(reel=("montant_ttc", "sum"))
    )

    budget = (
        df_bud_y
        .groupby("groupe_compte", as_index=False)
        .agg(budget=("budget", "sum"))
    )

    df_cmp = (
        budget
        .merge(reel, on="groupe_compte", how="outer")
        .fillna(0)
    )

    df_cmp["écart"] = df_cmp["budget"] - df_cmp["reel"]

    c1, c2, c3 = st.columns(3)
    c1.metric("Budget", euro(df_cmp["budget"].sum()))
    c2.metric("Réel", euro(df_cmp["reel"].sum()))
    c3.metric("Écart", euro(df_cmp["écart"].sum()))

    st.dataframe(
        df_cmp.rename(columns={
            "groupe_compte": "Groupe",
            "budget": "Budget (€)",
            "reel": "Réel (€)",
            "écart": "Écart (€)"
        }),
        use_container_width=True
    )

# =========================
# 📈 STATISTIQUES
# =========================
with tab_stats:
    st.subheader("📈 Statistiques")

    st.dataframe(
        df_f
        .groupby("poste", as_index=False)
        .agg(
            total=("montant_ttc", "sum"),
            nb=("id", "count")
        )
        .sort_values("total", ascending=False),
        use_container_width=True
    )

# =========================
# ✅ CONTRÔLE RÉPARTITION
# =========================
with tab_ctrl:
    st.subheader("✅ Contrôle de répartition")

    df_r = (
        df_rep
        .merge(df_dep[["id", "montant_ttc"]], left_on="depense_id", right_on="id")
    )

    df_r["montant_reparti"] = (
        df_r["montant_ttc"] * df_r["quote_part"] / BASE_TANTIEMES
    )

    ctrl = (
        df_r
        .groupby("depense_id", as_index=False)
        .agg(
            montant=("montant_ttc", "first"),
            reparti=("montant_reparti", "sum")
        )
    )

    ctrl["écart"] = ctrl["montant"] - ctrl["reparti"]

    anomalies = ctrl[ctrl["écart"].abs() > 0.01]

    if anomalies.empty:
        st.success("✅ Toutes les dépenses sont correctement réparties")
    else:
        st.error(f"❌ {len(anomalies)} anomalie(s)")
        st.dataframe(anomalies, use_container_width=True)