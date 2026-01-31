import streamlit as st
import pandas as pd

BASE_TANTIEMES = 10_000

def charges_par_lot_ui(supabase):
    st.title("🏠 Charges par lot")

    # =========================
    # Filtres
    # =========================
    annee = st.selectbox("Année", [2023, 2024, 2025, 2026], index=2)

    # =========================
    # Chargement lots
    # =========================
    lots_resp = (
        supabase
        .table("lots")
        .select("id, lot, tantiemes")
        .execute()
    )

    if not lots_resp.data:
        st.error("Aucun lot disponible (RLS ou table vide).")
        return

    df_lots = pd.DataFrame(lots_resp.data)

    lot_options = ["Tous"] + sorted(df_lots["lot"].tolist())
    lot_choice = st.selectbox("Lot", lot_options)

    # =========================
    # Chargement dépenses
    # =========================
    dep_resp = (
        supabase
        .table("depenses")
        .select("id, montant_ttc, compte")
        .eq("annee", annee)
        .execute()
    )

    if not dep_resp.data:
        st.warning("Aucune dépense pour cette année.")
        return

    df_dep = pd.DataFrame(dep_resp.data)

    # 🔗 Association comptes 71300100 ↔ 67800200
    df_dep["compte_groupe"] = df_dep["compte"].replace({
        "71300100": "67800200"
    })

    compte_options = ["Tous"] + sorted(df_dep["compte_groupe"].unique())
    compte_choice = st.selectbox("Compte", compte_options)

    # =========================
    # Répartition
    # =========================
    rep_resp = (
        supabase
        .table("repartition_depenses")
        .select("depense_id, lot_id, quote_part")
        .execute()
    )

    if not rep_resp.data:
        st.warning("Aucune répartition disponible.")
        return

    df_rep = pd.DataFrame(rep_resp.data)

    # =========================
    # Calcul
    # =========================
    df = (
        df_rep
        .merge(df_dep, left_on="depense_id", right_on="id")
        .merge(df_lots, left_on="lot_id", right_on="id", suffixes=("", "_lot"))
    )

    df["montant_lot"] = df["montant_ttc"] * df["quote_part"]

    # =========================
    # Filtres dynamiques
    # =========================
    if lot_choice != "Tous":
        df = df[df["lot"] == lot_choice]

    if compte_choice != "Tous":
        df = df[df["compte_groupe"] == compte_choice]

    # =========================
    # Agrégation
    # =========================
    df_sum = (
        df
        .groupby(["lot", "compte_groupe"], as_index=False)
        .agg(charges=("montant_lot", "sum"))
        .sort_values("charges", ascending=False)
    )

    total_global = df_sum["charges"].sum()
    df_sum["% immeuble"] = (df_sum["charges"] / total_global) * 100

    # =========================
    # KPI
    # =========================
    col1, col2, col3 = st.columns(3)

    col1.metric("Total charges (€)", f"{total_global:,.2f}")
    col2.metric("Nombre de lots", df_sum["lot"].nunique())
    col3.metric("Nombre de comptes", df_sum["compte_groupe"].nunique())

    st.caption(f"🔢 Répartition basée sur {BASE_TANTIEMES} tantièmes")

    # =========================
    # Tableau
    # =========================
    st.dataframe(
        df_sum.rename(columns={
            "lot": "Lot",
            "compte_groupe": "Compte",
            "charges": "Charges (€)"
        }),
        use_container_width=True
    )
