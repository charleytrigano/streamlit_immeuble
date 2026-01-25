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
    # LOAD LOTS
    # =========================
    lots_resp = supabase.table("lots").select("id, lot, tantiemes").execute()
    df_lots = pd.DataFrame(lots_resp.data)

    if df_lots.empty:
        st.error("Aucun lot trouvé.")
        return

    # 🔐 CAST EXPLICITE
    df_lots["id"] = df_lots["id"].astype(str)
    df_lots["lot"] = df_lots["lot"].astype(str)

    lot_filtre = st.sidebar.selectbox(
        "Lot",
        ["Tous"] + sorted(df_lots["lot"].unique().tolist())
    )

    # =========================
    # LOAD DEPENSES
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

    # 🔐 CAST EXPLICITE
    df_dep["lot_id"] = df_dep["lot_id"].astype(str)
    df_dep["compte"] = df_dep["compte"].astype(str)

    compte_filtre = st.sidebar.selectbox(
        "Compte",
        ["Tous"] + sorted(df_dep["compte"].dropna().unique().tolist())
    )

    if compte_filtre != "Tous":
        df_dep = df_dep[df_dep["compte"] == compte_filtre]

    # =========================
    # MERGE SÉCURISÉ
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
    # CHARGES RÉELLES
    # =========================
    charges_reelles = (
        df.groupby("lot", as_index=False)
        .agg(charges_reelles=("montant_ttc", "sum"))
    )

    # =========================
    # APPELS DE FONDS (désactivés proprement)
    # =========================
    charges_reelles["appels_fonds"] = 0
    charges_reelles["ecart"] = (
        charges_reelles["charges_reelles"]
        - charges_reelles["appels_fonds"]
    )

    # =========================
    # KPI
    # =========================
    col1, col2, col3 = st.columns(3)

    col1.metric(
        "Charges réelles totales",
        euro(charges_reelles["charges_reelles"].sum())
    )

    col2.metric(
        "Appels de fonds totaux",
        euro(0)
    )

    col3.metric(
        "Régularisation globale",
        euro(charges_reelles["ecart"].sum())
    )

    # =========================
    # TABLE
    # =========================
    st.markdown("### 📋 Régularisation par lot")
    st.caption("Répartition basée sur 10 000 tantièmes")

    display = charges_reelles.copy()
    display["charges_reelles"] = display["charges_reelles"].apply(euro)
    display["appels_fonds"] = display["appels_fonds"].apply(euro)
    display["ecart"] = display["ecart"].apply(euro)

    display = display.rename(columns={
        "lot": "Lot",
        "charges_reelles": "Charges réelles (€)",
        "appels_fonds": "Appels de fonds (€)",
        "ecart": "Écart (€)"
    })

    st.dataframe(display, use_container_width=True)

# =========================
# RUN
# =========================
if __name__ == "__main__":
    main()