import streamlit as st
import pandas as pd

BASE_TANTIEMES = 10_000

def charges_par_lot_ui(supabase):
    st.header("🏠 Charges par lot")

    annee = st.selectbox(
        "Année",
        [2023, 2024, 2025, 2026],
        index=2
    )

    # =========================
    # Chargement des lots
    # =========================
    lots_resp = (
        supabase
        .table("lots")
        .select("id, lot, tantiemes")
        .execute()
    )

    if not lots_resp.data:
        st.error(
            "❌ Aucun lot trouvé.\n\n"
            "👉 Vérifie que la table `lots` contient des données\n"
            "👉 et que le SELECT est autorisé (RLS)."
        )
        return

    df_lots = pd.DataFrame(lots_resp.data)

    # =========================
    # Chargement dépenses
    # =========================
    dep_resp = (
        supabase
        .table("depenses")
        .select("id, montant_ttc")
        .eq("annee", annee)
        .execute()
    )

    if not dep_resp.data:
        st.warning("Aucune dépense pour cette année.")
        return

    df_dep = pd.DataFrame(dep_resp.data)

    # =========================
    # Répartition (quote-part)
    # =========================
    rep_resp = (
        supabase
        .table("repartition_depenses")
        .select("depense_id, lot_id, quote_part")
        .execute()
    )

    if not rep_resp.data:
        st.warning("Aucune répartition enregistrée.")
        return

    df_rep = pd.DataFrame(rep_resp.data)

    # =========================
    # Calcul charges par lot
    # =========================
    df = (
        df_rep
        .merge(df_dep, left_on="depense_id", right_on="id")
        .merge(df_lots, left_on="lot_id", right_on="id", suffixes=("", "_lot"))
    )

    df["montant_lot"] = df["montant_ttc"] * df["quote_part"]

    df_lots_sum = (
        df
        .groupby(["lot", "tantiemes"], as_index=False)
        .agg(charges_totales=("montant_lot", "sum"))
        .sort_values("lot")
    )

    # =========================
    # Affichage
    # =========================
    st.caption(f"🔢 Répartition calculée sur une base de **{BASE_TANTIEMES} tantièmes**")

    st.dataframe(
        df_lots_sum.rename(columns={
            "lot": "Lot",
            "tantiemes": "Tantièmes",
            "charges_totales": "Charges (€)"
        }),
        use_container_width=True
    )