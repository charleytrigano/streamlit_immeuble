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

    # -------------------------
    # LOTS
    # -------------------------
    lots_resp = (
        supabase
        .table("lots")
        .select("id, lot, tantiemes")
        .execute()
    )
    df_lots = pd.DataFrame(lots_resp.data)

    if df_lots.empty:
        st.error("Aucun lot trouvé.")
        return

    df_lots["lot"] = df_lots["lot"].astype(str)

    lot_filtre = st.sidebar.selectbox(
        "Lot",
        ["Tous"] + sorted(df_lots["lot"].unique().tolist())
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

    df_dep["compte"] = df_dep["compte"].astype(str)

    compte_filtre = st.sidebar.selectbox(
        "Compte",
        ["Tous"] + sorted(df_dep["compte"].unique().tolist())
    )

    # =========================
    # RÉPARTITION DES DÉPENSES
    # =========================
    rep_resp = (
        supabase
        .table("repartition_depenses")
        .select("depense_id, lot_id, quote_part")
        .execute()
    )
    df_rep = pd.DataFrame(rep_resp.data)

    if df_rep.empty:
        st.error("Aucune répartition trouvée.")
        return

    # =========================
    # CALCUL DES CHARGES RÉELLES
    # =========================
    df = (
        df_rep
        .merge(df_dep, left_on="depense_id", right_on="id", how="left")
        .merge(df_lots, left_on="lot_id", right_on="id", how="left", suffixes=("", "_lot"))
    )

    if compte_filtre != "Tous":
        df = df[df["compte"] == compte_filtre]

    if lot_filtre != "Tous":
        df = df[df["lot"] == lot_filtre]

    df["charges_reelles"] = df["montant_ttc"] * df["quote_part"] / BASE_TANTIEMES

    charges_reelles = (
        df
        .groupby("lot", as_index=False)
        .agg(charges_reelles=("charges_reelles", "sum"))
    )

    # =========================
    # BUDGET / APPELS DE FONDS
    # =========================
    budget_resp = (
        supabase
        .table("budgets")
        .select("montant")
        .eq("annee", annee)
        .execute()
    )

    total_budget = sum(b["montant"] for b in budget_resp.data) if budget_resp.data else 0

    df_lots["appel_fonds"] = (
        total_budget * df_lots["tantiemes"] / BASE_TANTIEMES
    )

    if lot_filtre != "Tous":
        df_lots = df_lots[df_lots["lot"] == lot_filtre]

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
    # UI
    # =========================
    st.title("🏢 Pilotage des charges de l’immeuble")
    st.subheader("Charges par lot — Réel vs Appels de fonds")

    col1, col2, col3 = st.columns(3)

    col1.metric(
        "Charges réelles totales",
        f"{final['charges_reelles'].sum():,.2f} €".replace(",", " ").replace(".", ",")
    )
    col2.metric(
        "Appels de fonds totaux",
        f"{final['appel_fonds'].sum():,.2f} €".replace(",", " ").replace(".", ",")
    )
    col3.metric(
        "Régularisation globale",
        f"{final['ecart'].sum():,.2f} €".replace(",", " ").replace(".", ",")
    )

    st.markdown("### 📋 Régularisation par lot")
    st.caption("Répartition basée sur 10 000 tantièmes")

    st.dataframe(
        final.rename(columns={
            "lot": "Lot",
            "charges_reelles": "Charges réelles (€)",
            "appel_fonds": "Appels de fonds (€)",
            "ecart": "Écart (€)"
        }),
        use_container_width=True
    )

# =========================
# RUN
# =========================
if __name__ == "__main__":
    main()