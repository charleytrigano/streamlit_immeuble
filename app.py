import streamlit as st
import pandas as pd
from supabase import create_client

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
    return create_client(
        st.secrets["SUPABASE_URL"],
        st.secrets["SUPABASE_ANON_KEY"]
    )

# =========================
# FORMAT €
# =========================
def euro(val):
    if pd.isna(val):
        return "0,00 €"
    return f"{val:,.2f} €".replace(",", " ").replace(".", ",")

# =========================
# MAIN
# =========================
def main():
    supabase = get_supabase()

    st.title("🏢 Pilotage des charges de l’immeuble")
    st.subheader("Charges par lot — Réel vs Appels de fonds")

    # =========================
    # SIDEBAR
    # =========================
    st.sidebar.header("Filtres")

    annee = st.sidebar.selectbox(
        "Année",
        [2023, 2024, 2025, 2026],
        index=2
    )

    # =========================
    # LOTS
    # =========================
    lots_resp = supabase.table("lots").select(
        "id, lot, tantiemes"
    ).execute()

    df_lots = pd.DataFrame(lots_resp.data)

    if df_lots.empty:
        st.error("Aucun lot trouvé.")
        return

    df_lots["id"] = df_lots["id"].astype(str)
    df_lots["lot"] = df_lots["lot"].astype(str)
    df_lots["tantiemes"] = df_lots["tantiemes"].astype(float)

    lot_filtre = st.sidebar.selectbox(
        "Lot",
        ["Tous"] + sorted(df_lots["lot"].unique())
    )

    # =========================
    # DEPENSES
    # =========================
    dep_resp = (
        supabase
        .table("depenses")
        .select("montant_ttc, compte, lot_id")
        .eq("annee", annee)
        .execute()
    )

    df_dep = pd.DataFrame(dep_resp.data)

    if df_dep.empty:
        st.warning("Aucune dépense pour cette année.")
        return

    df_dep["lot_id"] = df_dep["lot_id"].astype(str)
    df_dep["compte"] = df_dep["compte"].astype(str)
    df_dep["montant_ttc"] = df_dep["montant_ttc"].astype(float)

    compte_filtre = st.sidebar.selectbox(
        "Compte",
        ["Tous"] + sorted(df_dep["compte"].dropna().unique())
    )

    if compte_filtre != "Tous":
        df_dep = df_dep[df_dep["compte"] == compte_filtre]

    # =========================
    # MERGE DEPENSES / LOTS
    # =========================
    df = df_dep.merge(
        df_lots,
        left_on="lot_id",
        right_on="id",
        how="left"
    )

    if lot_filtre != "Tous":
        df = df[df["lot"] == lot_filtre]

    # =========================
    # CHARGES RÉELLES PAR LOT
    # =========================
    charges = (
        df.groupby(["lot", "tantiemes"], as_index=False)
        .agg(charges_reelles=("montant_ttc", "sum"))
    )

    # =========================
    # BUDGET
    # =========================
    budget_resp = (
        supabase
        .table("budgets")
        .select("montant")
        .eq("annee", annee)
        .execute()
    )

    total_budget = sum(
        b["montant"] for b in budget_resp.data
    ) if budget_resp.data else 0

    # =========================
    # APPELS DE FONDS
    # =========================
    charges["appels_fonds"] = (
        total_budget
        * charges["tantiemes"]
        / BASE_TANTIEMES
    )

    charges["ecart"] = (
        charges["charges_reelles"]
        - charges["appels_fonds"]
    )

    # =========================
    # KPI
    # =========================
    col1, col2, col3 = st.columns(3)

    col1.metric(
        "Charges réelles totales",
        euro(charges["charges_reelles"].sum())
    )

    col2.metric(
        "Appels de fonds totaux",
        euro(charges["appels_fonds"].sum())
    )

    col3.metric(
        "Régularisation globale",
        euro(charges["ecart"].sum())
    )

    # =========================
    # TABLE
    # =========================
    st.markdown("### 📋 Régularisation par lot")
    st.caption("Répartition basée sur 10 000 tantièmes")

    table = charges.copy()
    table["charges_reelles"] = table["charges_reelles"].apply(euro)
    table["appels_fonds"] = table["appels_fonds"].apply(euro)
    table["ecart"] = table["ecart"].apply(euro)

    table = table.rename(columns={
        "lot": "Lot",
        "charges_reelles": "Charges réelles (€)",
        "appels_fonds": "Appels de fonds (€)",
        "ecart": "Écart (€)"
    })

    st.dataframe(table, use_container_width=True)

# =========================
# RUN
# =========================
if __name__ == "__main__":
    main()