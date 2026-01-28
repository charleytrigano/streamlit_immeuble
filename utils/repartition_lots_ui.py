import streamlit as st
import pandas as pd

BASE_TANTIEMES = 10_000


def repartition_lots_ui(supabase, annee):
    st.header("🏢 Répartition des charges par lot")

    # =========================
    # CHARGEMENT DES DONNÉES
    # =========================
    dep_resp = (
        supabase
        .table("depenses")
        .select("depense_id, montant_ttc, annee")
        .eq("annee", annee)
        .execute()
    )
    df_dep = pd.DataFrame(dep_resp.data)

    if df_dep.empty:
        st.info("Aucune dépense pour cette année.")
        return

    rep_resp = (
        supabase
        .table("repartition_depenses")
        .select("depense_id, lot_id, quote_part")
        .execute()
    )
    df_rep = pd.DataFrame(rep_resp.data)

    lots_resp = (
        supabase
        .table("lots")
        .select("lot_id, lot, tantiemes")
        .execute()
    )
    df_lots = pd.DataFrame(lots_resp.data)

    if df_rep.empty or df_lots.empty:
        st.warning("Données de répartition ou de lots manquantes.")
        return

    # =========================
    # MERGE LOGIQUE (CORRECT)
    # =========================
    df = (
        df_rep
        .merge(df_dep, on="depense_id", how="left")
        .merge(df_lots, on="lot_id", how="left")
    )

    # =========================
    # CALCUL DES CHARGES
    # =========================
    df["charges_reelles"] = (
        df["montant_ttc"] * df["quote_part"] / BASE_TANTIEMES
    )

    # =========================
    # AGRÉGATION PAR LOT
    # =========================
    recap = (
        df
        .groupby(["lot_id", "lot"], as_index=False)
        .agg(
            charges_reelles=("charges_reelles", "sum")
        )
        .sort_values("lot")
    )

    # =========================
    # AFFICHAGE
    # =========================
    st.dataframe(
        recap.rename(columns={
            "lot": "Lot",
            "charges_reelles": "Charges réelles (€)"
        }),
        use_container_width=True
    )