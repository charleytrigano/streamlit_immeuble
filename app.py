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
        st.error("Aucun lot trouvé dans la table lots.")
        return

    df_lots["lot"] = df_lots["lot"].astype(str)
    df_lots["tantiemes"] = df_lots["tantiemes"].astype(float)

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

    df_dep["montant_ttc"] = df_dep["montant_ttc"].astype(float)
    df_dep["compte"] = df_dep["compte"].fillna("Non renseigné").astype(str)

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
        st.error("Aucune répartition trouvée dans repartition_depenses.")
        return

    df_rep["quote_part"] = df_rep["quote_part"].astype(float)

    # =========================
    # MERGE GLOBAL (répartition + dépenses + lots)
    # =========================
    df = (
        df_rep
        .merge(df_dep, left_on="depense_id", right_on="id", how="left")
        .merge(
            df_lots,
            left_on="lot_id",
            right_on="id",
            how="left",
            suffixes=("", "_lot")
        )
    )

    # Si certaines lignes n'ont pas trouvé la dépense ou le lot, on les ignore
    df = df.dropna(subset=["montant_ttc", "lot"])

    # =========================
    # NORMALISATION DES QUOTE-PARTS
    # (on force somme = 1 par dépense)
    # =========================
    total_quote_par_depense = df.groupby("depense_id")["quote_part"].transform("sum")
    # éviter la division par zéro
    total_quote_par_depense = total_quote_par_depense.replace(0, 1)

    df["quote_norm"] = df["quote_part"] / total_quote_par_depense

    # =========================
    # CALCUL CHARGES RÉELLES
    # =========================
    df["charges_reelles"] = df["montant_ttc"] * df["quote_norm"]

    # =========================
    # APPLICATION DES FILTRES
    # =========================
    if compte_filtre != "Tous":
        df = df[df["compte"] == compte_filtre]

    if lot_filtre != "Tous":
        df = df[df["lot"] == lot_filtre]

    if df.empty:
        st.warning("Aucune ligne après application des filtres.")
        return

    # =========================
    # AGRÉGATION PAR LOT
    # =========================
    charges_lot = (
        df
        .groupby("lot", as_index=False)
        .agg(charges_reelles=("charges_reelles", "sum"))
    )

    # =========================
    # BUDGET / APPELS DE FONDS
    # =========================
    budgets_resp = (
        supabase
        .table("budgets")
        .select("annee, budget")
        .eq("annee", annee)
        .execute()
    )

    df_budgets = pd.DataFrame(budgets_resp.data)

    if not df_budgets.empty and "budget" in df_budgets.columns:
        budget_total = df_budgets["budget"].astype(float).sum()
    else:
        budget_total = 0.0

    df_lots["appel_fonds"] = budget_total * df_lots["tantiemes"] / BASE_TANTIEMES

    # on applique le filtre de lot sur les appels de fonds
    if lot_filtre != "Tous":
        df_lots_filtered = df_lots[df_lots["lot"] == lot_filtre].copy()
    else:
        df_lots_filtered = df_lots.copy()

    # =========================
    # TABLEAU FINAL PAR LOT
    # =========================
    final = (
        df_lots_filtered[["lot", "appel_fonds"]]
        .merge(charges_lot, on="lot", how="left")
        .fillna(0)
    )

    final["ecart"] = final["charges_reelles"] - final["appel_fonds"]

    # =========================
    # KPI
    # =========================
    st.title("🏢 Pilotage des charges de l’immeuble")
    st.subheader("Charges par lot — Réel vs Appels de fonds")

    total_charges_reelles = final["charges_reelles"].sum()
    total_appels = final["appel_fonds"].sum()
    total_ecart = final["ecart"].sum()

    col1, col2, col3 = st.columns(3)

    col1.metric(
        "Charges réelles totales",
        f"{total_charges_reelles:,.2f} €".replace(",", " ").replace(".", ",")
    )
    col2.metric(
        "Appels de fonds totaux",
        f"{total_appels:,.2f} €".replace(",", " ").replace(".", ",")
    )
    col3.metric(
        "Régularisation globale",
        f"{total_ecart:,.2f} €".replace(",", " ").replace(".", ",")
    )

    # =========================
    # RÉGULARISATION PAR LOT
    # =========================
    st.markdown("### 📋 Régularisation par lot")
    st.caption("Répartition basée sur les quote-parts (somme = 1 par dépense).")

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