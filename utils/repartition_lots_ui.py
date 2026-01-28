import streamlit as st
import pandas as pd

BASE_TANTIEMES = 10_000


def euro(x):
    return f"{x:,.2f} €".replace(",", " ").replace(".", ",")


def repartition_lots_ui(supabase, annee):
    st.header("🏢 Répartition des charges par lot")

    # ======================================================
    # CHARGEMENT DES DONNÉES
    # ======================================================
    dep = supabase.table("depenses").select("*").eq("annee", annee).execute().data
    rep = supabase.table("repartition_depenses").select("*").execute().data
    lots = supabase.table("lots").select("*").execute().data

    if not dep or not rep or not lots:
        st.warning("Données insuffisantes pour calculer la répartition.")
        return

    df_dep = pd.DataFrame(dep)
    df_rep = pd.DataFrame(rep)
    df_lots = pd.DataFrame(lots)

    # ======================================================
    # NORMALISATION DES CLÉS
    # ======================================================
    if "lot_id" not in df_lots.columns:
        st.error("❌ Colonne `lot_id` absente de la table lots")
        return

    if "lot_id" not in df_rep.columns:
        st.error("❌ Colonne `lot_id` absente de la table repartition_depenses")
        return

    if "depense_id" not in df_rep.columns:
        st.error("❌ Colonne `depense_id` absente de la table repartition_depenses")
        return

    if "depense_id" not in df_dep.columns:
        st.error("❌ Colonne `depense_id` absente de la table depenses")
        return

    # ======================================================
    # MERGE GLOBAL
    # ======================================================
    df = (
        df_rep
        .merge(df_dep, on="depense_id", how="left")
        .merge(df_lots, on="lot_id", how="left")
    )

    # ======================================================
    # CALCUL DES CHARGES
    # ======================================================
    df["charges_reelles"] = (
        df["montant_ttc"] * df["quote_part"] / BASE_TANTIEMES
    )

    # ======================================================
    # AGRÉGATION PAR LOT
    # ======================================================
    group_cols = ["lot_id"]

    # Ajout dynamique des colonnes descriptives si présentes
    for col in ["numero_lot", "etage", "usage", "proprietaire", "locataire"]:
        if col in df.columns:
            group_cols.append(col)

    result = (
        df
        .groupby(group_cols, as_index=False)
        .agg(charges_reelles=("charges_reelles", "sum"))
        .sort_values("charges_reelles", ascending=False)
    )

    # ======================================================
    # AFFICHAGE
    # ======================================================
    st.dataframe(
        result.rename(columns={
            "charges_reelles": "Charges réelles (€)"
        }),
        use_container_width=True
    )

    st.caption("Répartition calculée sur la base des tantièmes (10 000)")