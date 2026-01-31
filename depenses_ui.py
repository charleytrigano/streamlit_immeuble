import streamlit as st
import pandas as pd


def depenses_ui(supabase):
    st.title("💸 Dépenses")

    # -------------------------
    # Sélection année
    # -------------------------
    annee = st.selectbox(
        "Année",
        [2023, 2024, 2025, 2026],
        index=0
    )

    # -------------------------
    # Chargement des dépenses
    # -------------------------
    try:
        query = (
            supabase
            .table("depenses")
            .select(
                "depense_id, annee, date, compte, poste, fournisseur, "
                "montant_ttc, type, commentaire, lot_id"
            )
            .eq("annee", annee)
        )

        resp = query.execute()

    except Exception as e:
        st.error("❌ Erreur lors du chargement des dépenses")
        st.exception(e)
        return

    if not resp.data:
        st.warning("Aucune dépense pour cette année.")
        return

    df = pd.DataFrame(resp.data)

    # -------------------------
    # Mise en forme
    # -------------------------
    df = df.rename(columns={
        "depense_id": "ID",
        "date": "Date",
        "compte": "Compte",
        "poste": "Poste",
        "fournisseur": "Fournisseur",
        "montant_ttc": "Montant TTC (€)",
        "type": "Type",
        "commentaire": "Commentaire",
        "lot_id": "Lot"
    })

    df["Montant TTC (€)"] = df["Montant TTC (€)"].astype(float)

    # -------------------------
    # KPI
    # -------------------------
    total = df["Montant TTC (€)"].sum()

    st.metric("Total des dépenses (€)", f"{total:,.2f}")

    # -------------------------
    # Tableau
    # -------------------------
    st.dataframe(
        df.sort_values("Date", ascending=False),
        use_container_width=True
    )