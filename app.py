import streamlit as st
import pandas as pd
from supabase import create_client

# =========================
# CONFIG
# =========================
BASE_TANTIEMES = 10_000

st.set_page_config(
    page_title="Pilotage des charges",
    layout="wide"
)

# =========================
# SUPABASE
# =========================
@st.cache_resource
def get_supabase():
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_ANON_KEY"]
    return create_client(url, key)

supabase = get_supabase()

# =========================
# UTILS
# =========================
def eur(x):
    return f"{x:,.2f} €".replace(",", " ").replace(".", ",")

# =========================
# SIDEBAR
# =========================
st.sidebar.title("Filtres")

annee = st.sidebar.selectbox(
    "Année",
    [2023, 2024, 2025, 2026],
    index=2
)

# =========================
# CHARGEMENT DES LOTS
# =========================
lots_resp = (
    supabase
    .table("lots")
    .select("id, lot, tantiemes")
    .execute()
)

if not lots_resp.data:
    st.error("Aucun lot trouvé.")
    st.stop()

df_lots = pd.DataFrame(lots_resp.data)

lot_filtre = st.sidebar.selectbox(
    "Lot",
    ["Tous"] + df_lots["lot"].astype(str).tolist()
)

# =========================
# DEPENSES
# =========================
dep_resp = (
    supabase
    .table("depenses")
    .select("id, annee, montant_ttc, compte")
    .eq("annee", annee)
    .execute()
)

if not dep_resp.data:
    st.warning("Aucune dépense pour cette année.")
    st.stop()

df_dep = pd.DataFrame(dep_resp.data)

compte_filtre = st.sidebar.selectbox(
    "Compte",
    ["Tous"] + sorted(df_dep["compte"].dropna().astype(str).unique().tolist())
)

# =========================
# REPARTITION DES DEPENSES
# =========================
rep_resp = (
    supabase
    .table("repartition_depenses")
    .select("depense_id, lot_id, quote_part")
    .execute()
)

if not rep_resp.data:
    st.error("Aucune répartition trouvée.")
    st.stop()

df_rep = pd.DataFrame(rep_resp.data)

# jointures
df = (
    df_rep
    .merge(df_dep, left_on="depense_id", right_on="id", how="left")
    .merge(df_lots, left_on="lot_id", right_on="id", how="left", suffixes=("", "_lot"))
)

# filtres
if lot_filtre != "Tous":
    df = df[df["lot"].astype(str) == lot_filtre]

if compte_filtre != "Tous":
    df = df[df["compte"].astype(str) == compte_filtre]

# calcul réel
df["charge_reelle"] = df["montant_ttc"] * df["quote_part"]

charges_reelles = (
    df
    .groupby("lot", as_index=False)
    .agg(charges_reelles=("charge_reelle", "sum"))
)

# =========================
# BUDGET / APPELS DE FONDS
# =========================
budget_resp = (
    supabase
    .table("budget")
    .select("annee, budget")
    .eq("annee", annee)
    .execute()
)

total_budget = sum(b["budget"] for b in budget_resp.data) if budget_resp.data else 0

df_lots["appel_fonds"] = (
    total_budget * df_lots["tantiemes"] / BASE_TANTIEMES
)

if lot_filtre != "Tous":
    df_lots = df_lots[df_lots["lot"].astype(str) == lot_filtre]

# =========================
# FINAL
# =========================
final = (
    df_lots[["lot", "appel_fonds"]]
    .merge(charges_reelles, on="lot", how="left")
    .fillna(0)
)

final["ecart"] = final["charges_reelles"] - final["appel_fonds"]

# =========================
# AFFICHAGE
# =========================
st.title("🏢 Pilotage des charges de l’immeuble")
st.subheader("Charges par lot — Réel vs Appels de fonds")

col1, col2, col3 = st.columns(3)

col1.metric(
    "Charges réelles totales",
    eur(final["charges_reelles"].sum())
)

col2.metric(
    "Appels de fonds totaux",
    eur(final["appel_fonds"].sum())
)

col3.metric(
    "Régularisation globale",
    eur(final["ecart"].sum())
)

st.caption("Répartition basée sur 10 000 tantièmes")

# tableau
st.subheader("📋 Régularisation par lot")

st.dataframe(
    final.rename(columns={
        "lot": "Lot",
        "charges_reelles": "Charges réelles (€)",
        "appel_fonds": "Appels de fonds (€)",
        "ecart": "Écart (€)"
    }).assign(
        **{
            "Charges réelles (€)": lambda d: d["Charges réelles (€)"].map(eur),
            "Appels de fonds (€)": lambda d: d["Appels de fonds (€)"].map(eur),
            "Écart (€)": lambda d: d["Écart (€)"].map(eur),
        }
    ),
    use_container_width=True
)