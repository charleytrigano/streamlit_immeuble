
import streamlit as st
import pandas as pd

BASE_REPARTITION = 10000  # les quote_part sont en 1 / 10 000


def charges_par_lot_ui(supabase):
    st.title("🏠 Charges par lot")

    # -------------------------
    # Sélection de l'année
    # -------------------------
    annee = st.selectbox("Année", [2023, 2024, 2025, 2026], index=0)

    # -------------------------
    # Dépenses
    # -------------------------
    dep_resp = (
        supabase
        .table("depenses")
        .select("id, annee, montant_ttc, compte")
        .eq("annee", annee)
        .execute()
    )

    if not dep_resp.data:
        st.warning("Aucune dépense pour cette année.")
        return

    df_dep = pd.DataFrame(dep_resp.data)
    df_dep["compte"] = df_dep["compte"].astype(str)

    # -------------------------
    # Répartitions
    # -------------------------
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

    # -------------------------
    # Lots
    # -------------------------
    lots_resp = (
        supabase
        .table("lots")
        .select("id, lot, tantiemes, batiment, etage, usage, description")
        .execute()
    )

    if not lots_resp.data:
        st.warning("Aucun lot trouvé dans la table lots.")
        return

    df_lots = pd.DataFrame(lots_resp.data)

    # -------------------------
    # Jointure dépenses ↔ répartitions ↔ lots
    # -------------------------
    df = df_rep.merge(
        df_dep,
        left_on="depense_id",
        right_on="id",
        how="inner"
    )

    df = df.merge(
        df_lots,
        left_on="lot_id",
        right_on="id",
        how="left",
        suffixes=("_dep", "_lot")
    )

    # -------------------------
    # Règle 71300100 → 67800200
    # -------------------------
    df["compte_affiche"] = df["compte"]
    df.loc[df["compte_affiche"] == "71300100", "compte_affiche"] = "67800200"

    # -------------------------
    # Calcul du montant réparti
    # -------------------------
    df["quote_norm"] = df["quote_part"] / BASE_REPARTITION
    df["montant_reparti"] = df["montant_ttc"] * df["quote_norm"]

    # -------------------------
    # Vue 1 : total des charges par lot
    # -------------------------
    df_lot = (
        df.groupby(["lot_id", "lot"], as_index=False)
        .agg(
            charges_totales=("montant_reparti", "sum"),
            tantiemes=("tantiemes", "first"),
            batiment=("batiment", "first"),
            usage=("usage", "first"),
        )
    )

    df_lot["charges_par_tantieme"] = df_lot["charges_totales"] / df_lot["tantiemes"].replace(0, pd.NA)

    st.subheader("Résumé par lot")
    st.dataframe(
        df_lot.rename(columns={
            "lot": "Lot",
            "charges_totales": "Charges totales (€)",
            "tantiemes": "Tantièmes",
            "batiment": "Bâtiment",
            "usage": "Usage",
            "charges_par_tantieme": "Charges / tantième (€)",
        }),
        use_container_width=True,
    )

    # -------------------------
    # Vue 2 : détail des charges par lot et par compte
    # (avec la règle 71300100 → 67800200 appliquée)
    # -------------------------
    st.subheader("Détail par lot et par compte")

    df_lot_compte = (
        df.groupby(["lot_id", "lot", "compte_affiche"], as_index=False)
        .agg(charges=("montant_reparti", "sum"))
    )

    st.dataframe(
        df_lot_compte.rename(columns={
            "lot": "Lot",
            "compte_affiche": "Compte",
            "charges": "Montant (€)",
        }),
        use_container_width=True,
    )

    # -------------------------
    # KPI globaux
    # -------------------------
    total_charges = df["montant_reparti"].sum()
    nb_lots = df_lot["lot_id"].nunique()

    col1, col2 = st.columns(2)
    col1.metric("Total charges réparties (€)", f"{total_charges:,.2f}")
    col2.metric("Nombre de lots", nb_lots)