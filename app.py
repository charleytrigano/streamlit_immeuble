import streamlit as st
import pandas as pd
from supabase import create_client

# =========================
# CONFIG
# =========================
BASE_TANTIEMES = 10_000

st.set_page_config(
    page_title="Pilotage des charges de l’immeuble",
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

    # -------------------------
    # LOTS
    # -------------------------
    lots_resp = supabase.table("lots").select("id, lot, tantiemes").execute()
    df_lots = pd.DataFrame(lots_resp.data)

    if df_lots.empty:
        st.error("Aucun lot trouvé.")
        return

    df_lots["lot"] = df_lots["lot"].astype(str)

    lot_filtre = st.sidebar.selectbox(
        "Lot",
        ["Tous"] + sorted(df_lots["lot"].unique())
    )

    # -------------------------
    # DÉPENSES (de l'année)
    # -------------------------
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
        ["Tous"] + sorted(df_dep["compte"].dropna().unique())
    )

    # Filtre compte côté dépenses
    if compte_filtre != "Tous":
        df_dep = df_dep[df_dep["compte"] == compte_filtre]

    if df_dep.empty:
        st.warning("Aucune dépense après filtrage par compte.")
        return

    # -------------------------
    # RÉPARTITION DES DÉPENSES
    # -------------------------
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

    # Nettoyage / typage
    df_rep["quote_part"] = pd.to_numeric(df_rep["quote_part"], errors="coerce").fillna(0)

    # -------------------------
    # JOINTURE RÉPARTITION + DÉPENSES
    # -------------------------
    df = df_rep.merge(
        df_dep,
        left_on="depense_id",
        right_on="id",
        how="inner"
    )

    if df.empty:
        st.warning("Aucune dépense de cette année n'a de répartition.")
        return

    # =========================
    # NORMALISATION DES QUOTES-PARTS
    # =========================
    # Pour chaque dépense, on force la somme des quote_part à 1
    sum_quote = (
        df.groupby("depense_id", as_index=False)
          .agg(sum_quote=("quote_part", "sum"))
    )

    df = df.merge(sum_quote, on="depense_id", how="left")

    # évite division par zéro : si sum_quote == 0, on met 0 partout
    df["effective_share"] = 0.0
    mask_non_zero = df["sum_quote"] != 0
    df.loc[mask_non_zero, "effective_share"] = (
        df.loc[mask_non_zero, "quote_part"] / df.loc[mask_non_zero, "sum_quote"]
    )

    # -------------------------
    # JOINTURE AVEC LOTS
    # -------------------------
    df = df.merge(
        df_lots,
        left_on="lot_id",
        right_on="id",
        how="left",
        suffixes=("", "_lot")
    )

    # Filtre lot éventuel
    if lot_filtre != "Tous":
        df = df[df["lot"] == lot_filtre]

    if df.empty:
        st.warning("Aucune ligne après filtrage par lot / compte.")
        return

    # =========================
    # CALCUL CHARGES RÉELLES
    # =========================
    # Ici la somme des effective_share par dépense = 1,
    # donc la somme des charges_reelles = somme des montants TTC des dépenses réparties.
    df["charges_reelles"] = df["montant_ttc"] * df["effective_share"]

    charges_reelles = (
        df.groupby("lot", as_index=False)
          .agg(charges_reelles=("charges_reelles", "sum"))
    )

    # Total théorique des dépenses réparties (doit = somme charges_reelles)
    dep_ids_reparties = df["depense_id"].unique()
    total_depenses_reparties = df_dep[df_dep["id"].isin(dep_ids_reparties)]["montant_ttc"].sum()

    # =========================
    # BUDGET / APPELS DE FONDS
    # =========================
    budget_resp = (
        supabase
        .table("budgets")
        .select("budget")
        .eq("annee", annee)
        .execute()
    )

    total_budget = sum(b["budget"] for b in budget_resp.data) if budget_resp.data else 0.0

    df_lots_budget = df_lots.copy()
    df_lots_budget["appel_fonds"] = (
        total_budget * df_lots_budget["tantiemes"] / BASE_TANTIEMES
    )

    if lot_filtre != "Tous":
        df_lots_budget = df_lots_budget[df_lots_budget["lot"] == lot_filtre]

    # =========================
    # TABLE FINALE PAR LOT
    # =========================
    final = (
        df_lots_budget[["lot", "appel_fonds"]]
        .merge(charges_reelles, on="lot", how="left")
        .fillna(0)
    )

    final["ecart"] = final["charges_reelles"] - final["appel_fonds"]

    # =========================
    # UI
    # =========================
    st.title("🏢 Pilotage des charges de l’immeuble")
    st.subheader("Charges par lot — Réel vs Appels de fonds")

    col1, col2, col3, col4 = st.columns(4)

    col1.metric(
        "Dépenses réparties (théoriques)",
        eur(total_depenses_reparties)
    )
    col2.metric(
        "Charges réelles totales",
        eur(final["charges_reelles"].sum())
    )
    col3.metric(
        "Appels de fonds totaux",
        eur(final["appel_fonds"].sum())
    )
    col4.metric(
        "Régularisation globale",
        eur(final["ecart"].sum())
    )

    st.markdown("### 📋 Détail par lot")
    st.caption("Répartition basée sur les quotes-parts normalisées (somme = 1 par dépense)")

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