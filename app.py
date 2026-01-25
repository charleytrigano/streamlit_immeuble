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
    return create_client(
        st.secrets["SUPABASE_URL"],
        st.secrets["SUPABASE_ANON_KEY"]
    )

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
    lots_resp = (
        supabase
        .table("lots")
        .select("id, lot, tantiemes")
        .execute()
    )
    df_lots = pd.DataFrame(lots_resp.data)

    if df_lots.empty:
        st.error("Aucun lot trouvé")
        return

    df_lots["lot"] = df_lots["lot"].astype(str)

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
        st.warning("Aucune dépense pour cette année")
        return

    df_dep["compte"] = df_dep["compte"].fillna("Non renseigné")

    compte_filtre = st.sidebar.selectbox(
        "Compte",
        ["Tous"] + sorted(df_dep["compte"].unique())
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
        st.error("Aucune répartition trouvée")
        return

    # =========================
    # MERGE GLOBAL
    # =========================
    df = (
        df_rep
        .merge(df_dep, left_on="depense_id", right_on="id", how="left")
        .merge(df_lots, left_on="lot_id", right_on="id", how="left", suffixes=("", "_lot"))
    )

    # =========================
    # FILTRES DATA
    # =========================
    if compte_filtre != "Tous":
        df = df[df["compte"] == compte_filtre]

    if lot_filtre != "Tous":
        df = df[df["lot"] == lot_filtre]

    # =========================
    # CALCUL CHARGES RÉELLES
    # =========================
    df["charges_reelles"] = df["montant_ttc"] * df["quote_part"] / BASE_TANTIEMES

    charges_lot = (
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

    budget_total = sum(b["montant"] for b in budget_resp.data) if budget_resp.data else 0

    df_lots["appel_fonds"] = (
        budget_total * df_lots["tantiemes"] / BASE_TANTIEMES
    )

    if lot_filtre != "Tous":
        df_lots = df_lots[df_lots["lot"] == lot_filtre]

    # =========================
    # TABLEAU FINAL PAR LOT
    # =========================
    final = (
        df_lots[["lot", "appel_fonds"]]
        .merge(charges_lot, on="lot", how="left")
        .fillna(0)
    )

    final["ecart"] = final["charges_reelles"] - final["appel_fonds"]

    # =========================
    # KPI
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

    # =========================
    # TABLEAU PAR LOT
    # =========================
    st.markdown("### 📋 Régularisation par lot")

    st.dataframe(
        final.rename(columns={
            "lot": "Lot",
            "appel_fonds": "Appels de fonds (€)",
            "charges_reelles": "Charges réelles (€)",
            "ecart": "Écart (€)"
        }),
        use_container_width=True
    )

    # =========================
    # DÉTAIL DES DÉPENSES PAR COMPTE
    # =========================
    st.markdown("### 📊 Détail des dépenses par compte")

    dep_compte = (
        df
        .groupby("compte", as_index=False)
        .agg(
            montant_total=("montant_ttc", "sum"),
            charges_reelles=("charges_reelles", "sum")
        )
        .sort_values("charges_reelles", ascending=False)
    )

    st.dataframe(
        dep_compte.rename(columns={
            "compte": "Compte",
            "montant_total": "Montant total facturé (€)",
            "charges_reelles": "Charges réelles réparties (€)"
        }),
        use_container_width=True
    )


# =========================
# RUN
# =========================
if __name__ == "__main__":
    main()