
import streamlit as st
import pandas as pd


def euro(x):
    return f"{x:,.2f} €".replace(",", " ").replace(".", ",")


def repartition_lots_ui(supabase, annee):
    st.header("🏢 Répartition des charges par lot")

    # ======================================================
    # CHARGEMENT DES DONNÉES
    # ======================================================
    df_dep = pd.DataFrame(
        supabase
        .table("depenses")
        .select("*")
        .eq("annee", annee)
        .execute()
        .data
    )

    df_lots = pd.DataFrame(
        supabase
        .table("lots")
        .select("*")
        .execute()
        .data
    )

    if df_dep.empty or df_lots.empty:
        st.warning("Données insuffisantes pour la répartition.")
        return

    df_dep["montant_ttc"] = pd.to_numeric(df_dep["montant_ttc"], errors="coerce").fillna(0)
    df_lots["tantiemes"] = pd.to_numeric(df_lots["tantiemes"], errors="coerce").fillna(0)

    total_tantiemes = df_lots["tantiemes"].sum()

    # ======================================================
    # 1️⃣ CHARGES DIRECTES PAR LOT
    # ======================================================
    df_direct = df_dep[df_dep["lot_id"].notna()].copy()

    df_direct = df_direct.merge(
        df_lots[["id", "lot"]],
        left_on="lot_id",
        right_on="id",
        how="left"
    )

    df_direct["charge_lot"] = df_direct["montant_ttc"]

    # ======================================================
    # 2️⃣ CHARGES À RÉPARTIR (TANTIÈMES)
    # ======================================================
    df_rep = df_dep[
        df_dep["lot_id"].isna() &
        (df_dep["repartition_requise"] == True)
    ].copy()

    if not df_rep.empty and total_tantiemes > 0:
        df_rep["key"] = 1
        df_lots["key"] = 1

        df_rep = df_rep.merge(df_lots, on="key")

        df_rep["charge_lot"] = (
            df_rep["montant_ttc"] * df_rep["tantiemes"] / total_tantiemes
        )

        df_rep = df_rep.rename(columns={"lot": "lot"})
    else:
        df_rep = pd.DataFrame(columns=["lot", "charge_lot"])

    # ======================================================
    # CONSOLIDATION
    # ======================================================
    df_all = pd.concat([
        df_direct[["lot", "charge_lot"]],
        df_rep[["lot", "charge_lot"]]
    ])

    # ======================================================
    # TOTAL PAR LOT
    # ======================================================
    synthese = (
        df_all
        .groupby("lot", as_index=False)
        .agg(charges_reelles=("charge_lot", "sum"))
        .sort_values("lot")
    )

    # ======================================================
    # KPI
    # ======================================================
    col1, col2 = st.columns(2)

    col1.metric(
        "💸 Total charges réparties",
        euro(synthese["charges_reelles"].sum())
    )

    col2.metric(
        "🏢 Nombre de lots",
        synthese["lot"].nunique()
    )

    # ======================================================
    # TABLEAU SYNTHÈSE
    # ======================================================
    st.subheader("📋 Charges réelles par lot")

    st.dataframe(
        synthese.rename(columns={
            "lot": "Lot",
            "charges_reelles": "Charges réelles (€)"
        }),
        use_container_width=True
    )

    # ======================================================
    # DÉTAIL PAR LOT
    # ======================================================
    st.subheader("🔍 Détail par lot")

    lot_sel = st.selectbox("Lot", sorted(synthese["lot"].unique()))

    detail = df_all[df_all["lot"] == lot_sel]

    st.metric(
        f"Total charges – Lot {lot_sel}",
        euro(detail["charge_lot"].sum())
    )

    st.dataframe(
        detail.rename(columns={
            "charge_lot": "Montant (€)"
        }),
        use_container_width=True
    )