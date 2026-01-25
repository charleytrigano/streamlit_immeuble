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
    df_lots = pd.DataFrame(
        supabase.table("lots").select("id, lot, tantiemes").execute().data
    )
    df_lots["lot"] = df_lots["lot"].astype(str)

    lot_filtre = st.sidebar.selectbox(
        "Lot",
        ["Tous"] + sorted(df_lots["lot"].tolist())
    )

    # =========================
    # DEPENSES
    # =========================
    df_dep = pd.DataFrame(
        supabase
        .table("depenses")
        .select("id, annee, compte, montant_ttc, lot_id")
        .eq("annee", annee)
        .execute()
        .data
    )

    df_dep["compte"] = df_dep["compte"].astype(str)

    compte_filtre = st.sidebar.selectbox(
        "Compte",
        ["Tous"] + sorted(df_dep["compte"].unique().tolist())
    )

    # =========================
    # REPARTITIONS
    # =========================
    df_rep = pd.DataFrame(
        supabase
        .table("repartition_depenses")
        .select("depense_id, lot_id, quote_part")
        .execute()
        .data
    )

    # =========================
    # C — AFFECTATION DIRECTE
    # =========================
    direct = df_dep[df_dep["lot_id"].notna()].copy()

    direct = direct.merge(
        df_lots,
        left_on="lot_id",
        right_on="id",
        how="left",
        suffixes=("", "_lot")
    )

    direct["charges"] = direct["montant_ttc"]

    direct = direct[["lot", "compte", "charges"]]

    # =========================
    # A — REPARTITION PAR CLE
    # =========================
    rep = df_rep.merge(
        df_dep[df_dep["lot_id"].isna()],
        left_on="depense_id",
        right_on="id",
        how="left",
        suffixes=("", "_dep")
    )

    # RENOMMAGE EXPLICITE (clé de la correction)
    rep = rep.rename(columns={
        "lot_id": "lot_id_rep"
    })

    rep = rep.merge(
        df_lots,
        left_on="lot_id_rep",
        right_on="id",
        how="left",
        suffixes=("", "_lot")
    )

    rep["charges"] = rep["montant_ttc"] * rep["quote_part"] / BASE_TANTIEMES

    rep = rep[["lot", "compte", "charges"]]

    # =========================
    # UNION A + C
    # =========================
    charges = pd.concat([direct, rep], ignore_index=True)

    if compte_filtre != "Tous":
        charges = charges[charges["compte"] == compte_filtre]

    if lot_filtre != "Tous":
        charges = charges[charges["lot"] == lot_filtre]

    charges_lot = (
        charges
        .groupby("lot", as_index=False)
        .agg(charges_reelles=("charges", "sum"))
    )

    # =========================
    # BUDGET / APPELS
    # =========================
    budget_total = sum(
        b["montant"]
        for b in supabase
        .table("budgets")
        .select("montant")
        .eq("annee", annee)
        .execute()
        .data
    )

    df_lots["appel_fonds"] = (
        budget_total * df_lots["tantiemes"] / BASE_TANTIEMES
    )

    # =========================
    # FINAL
    # =========================
    final = df_lots.merge(charges_lot, on="lot", how="left").fillna(0)
    final["ecart"] = final["charges_reelles"] - final["appel_fonds"]

    # =========================
    # UI
    # =========================
    st.title("🏢 Pilotage des charges de l’immeuble")

    col1, col2, col3 = st.columns(3)

    def euro(x):
        return f"{x:,.2f} €".replace(",", " ").replace(".", ",")

    col1.metric("Charges réelles", euro(final["charges_reelles"].sum()))
    col2.metric("Appels de fonds", euro(final["appel_fonds"].sum()))
    col3.metric("Régularisation", euro(final["ecart"].sum()))

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