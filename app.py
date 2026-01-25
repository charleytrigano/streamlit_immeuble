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

# =========================
# FORMAT €
# =========================
def eur(x: float) -> str:
    return f"{x:,.2f} €".replace(",", " ").replace(".", ",")

# =========================
# MAIN
# =========================
def main():
    supabase = get_supabase()

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
    # LOTS
    # =========================
    lots_resp = supabase.table("lots").select("id, lot, tantiemes").execute()
    df_lots = pd.DataFrame(lots_resp.data)

    if df_lots.empty:
        st.error("Aucun lot trouvé.")
        return

    df_lots["lot"] = df_lots["lot"].astype(str)
    df_lots["tantiemes"] = pd.to_numeric(df_lots["tantiemes"], errors="coerce").fillna(0)

    lot_filtre = st.sidebar.selectbox(
        "Lot",
        ["Tous"] + sorted(df_lots["lot"].unique())
    )

    # =========================
    # DÉPENSES
    # =========================
    dep_resp = (
        supabase
        .table("depenses")
        .select("id, montant_ttc, compte, annee")
        .eq("annee", annee)
        .execute()
    )
    df_dep = pd.DataFrame(dep_resp.data)

    if df_dep.empty:
        st.warning("Aucune dépense pour cette année.")
        return

    df_dep["montant_ttc"] = pd.to_numeric(df_dep["montant_ttc"], errors="coerce").fillna(0)
    df_dep["compte"] = df_dep["compte"].astype(str)

    # =========================
    # FILTRE COMPTE
    # =========================
    compte_filtre = st.sidebar.selectbox(
        "Compte",
        ["Tous"] + sorted(df_dep["compte"].dropna().unique())
    )

    if compte_filtre != "Tous":
        df_dep = df_dep[df_dep["compte"] == compte_filtre]

    if df_dep.empty:
        st.warning("Aucune dépense après filtrage.")
        return

    # =========================
    # TOTAL CHARGES FILTRÉ
    # =========================
    total_charges_filtre = df_dep["montant_ttc"].sum()

    # =========================
    # BUDGETS
    # =========================
    bud_resp = (
        supabase
        .table("budgets")
        .select("annee, budget")
        .eq("annee", annee)
        .execute()
    )
    df_bud = pd.DataFrame(bud_resp.data) if bud_resp.data else pd.DataFrame(columns=["budget"])
    df_bud["budget"] = pd.to_numeric(df_bud["budget"], errors="coerce").fillna(0)

    total_budget = df_bud["budget"].sum()

    # =========================
    # RÉPARTITION PAR LOT
    # =========================
    df = df_lots.copy()
    df["part"] = df["tantiemes"] / BASE_TANTIEMES

    df["charges_reelles"] = total_charges_filtre * df["part"]
    df["appel_fonds"] = total_budget * df["part"]
    df["ecart"] = df["charges_reelles"] - df["appel_fonds"]

    # =========================
    # FILTRE LOT (APRÈS CALCUL)
    # =========================
    if lot_filtre != "Tous":
        df = df[df["lot"] == lot_filtre]

    # =========================
    # KPI (ALIGNÉS AVEC FILTRES)
    # =========================
    st.title("🏢 Pilotage des charges de l’immeuble")
    st.subheader("Charges par lot — Réel vs Appels de fonds")

    col1, col2, col3 = st.columns(3)

    col1.metric(
        "Charges réelles (filtrées)",
        eur(df["charges_reelles"].sum())
    )
    col2.metric(
        "Appels de fonds",
        eur(df["appel_fonds"].sum())
    )
    col3.metric(
        "Régularisation",
        eur(df["ecart"].sum())
    )

    # =========================
    # TABLEAU
    # =========================
    st.markdown("### 📋 Détail par lot")
    st.caption("Répartition proratisée sur 10 000 tantièmes")

    df_aff = df[["lot", "appel_fonds", "charges_reelles", "ecart"]].copy()
    df_aff.rename(columns={
        "lot": "Lot",
        "appel_fonds": "Appels de fonds (€)",
        "charges_reelles": "Charges réelles (€)",
        "ecart": "Écart (€)"
    }, inplace=True)

    for col in df_aff.columns[1:]:
        df_aff[col] = df_aff[col].apply(eur)

    st.dataframe(df_aff, use_container_width=True)


# =========================
# DÉTAIL DES DÉPENSES PAR COMPTE
# =========================
st.markdown("### 📊 Détail des dépenses par compte")
st.caption("Basé sur les dépenses filtrées (avant répartition par lot)")

df_compte = (
   
    .groupby("compte", as_index=False)
    .agg(montant=("montant_ttc", "sum"))
    .sort_values("montant", ascending=False)
)

df_compte["part (%)"] = (
    df_compte["montant"] / df_compte["montant"].sum() * 100
)

df_compte_aff = df_compte.copy()
df_compte_aff["montant"] = df_compte_aff["montant"].apply(eur)
df_compte_aff["part (%)"] = df_compte_aff["part (%)"].round(2)

df_compte_aff.rename(columns={
    "compte": "Compte",
    "montant": "Montant (€)",
}, inplace=True)

st.dataframe(
    df_compte_aff,
    use_container_width=True
)

# =========================
# RUN
# =========================
if __name__ == "__main__":
    main()
