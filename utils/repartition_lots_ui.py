import streamlit as st
import pandas as pd

BASE_TANTIEMES = 10_000


def euro(x):
    return f"{x:,.2f} €".replace(",", " ").replace(".", ",")


def find_common_key(df1, df2, candidates):
    """Retourne la première colonne commune trouvée"""
    for c in candidates:
        if c in df1.columns and c in df2.columns:
            return c
    return None


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
    # CLÉS DE JOINTURE (AUTO-DÉTECTION)
    # ======================================================
    dep_key = find_common_key(
        df_rep,
        df_dep,
        ["depense_id", "depense_uuid", "id"]
    )

    lot_key = find_common_key(
        df_rep,
        df_lots,
        ["lot_id", "lot", "lot_uuid", "id"]
    )

    if not dep_key:
        st.error("❌ Impossible de relier les dépenses à la répartition (clé manquante).")
        st.stop()

    if not lot_key:
        st.error("❌ Impossible de relier les lots à la répartition (clé manquante).")
        st.stop()

    # ======================================================
    # MERGE GLOBAL
    # ======================================================
    df = (
        df_rep
        .merge(df_dep, on=dep_key, how="left")
        .merge(df_lots, on=lot_key, how="left", suffixes=("", "_lot"))
    )

    # ======================================================
    # CONTRÔLES
    # ======================================================
    if "montant_ttc" not in df.columns or "quote_part" not in df.columns:
        st.error("❌ Colonnes nécessaires absentes (montant_ttc / quote_part).")
        st.stop()

    # ======================================================
    # CALCUL DES CHARGES
    # ======================================================
    df["charges_reelles"] = (
        df["montant_ttc"] * df["quote_part"] / BASE_TANTIEMES
    )

    # ======================================================
    # COLONNES DESCRIPTIVES LOT
    # ======================================================
    lot_cols = []
    for c in ["numero_lot", "lot", "etage", "usage", "proprietaire", "locataire"]:
        if c in df.columns:
            lot_cols.append(c)

    group_cols = [lot_key] + lot_cols

    # ======================================================
    # AGRÉGATION
    # ======================================================
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

    st.caption("Répartition calculée à partir des tantièmes (base 10 000)")