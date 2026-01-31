import streamlit as st
import pandas as pd


def depenses_ui(supabase):
    st.header("💸 Dépenses")

    # -------------------------
    # Sélection de l’année
    # -------------------------
    annee = st.selectbox(
        "Année",
        [2023, 2024, 2025, 2026],
        index=1
    )

    # -------------------------
    # Chargement des dépenses
    # -------------------------
    resp = (
        supabase
        .table("depenses")
        .select("""
            depense_id,
            annee,
            compte,
            poste,
            fournisseur,
            montant_ttc,
            date_depense
        """)
        .eq("annee", annee)
        .order("date_depense", desc=False)
        .execute()
    )

    if not resp.data:
        st.info("Aucune dépense pour cette année.")
        return

    df = pd.DataFrame(resp.data)

    # -------------------------
    # Mise en forme
    # -------------------------
    df["date_depense"] = pd.to_datetime(df["date_depense"])
    df["montant_ttc"] = df["montant_ttc"].astype(float)

    df_view = df.rename(columns={
        "depense_id": "ID",
        "date_depense": "Date",
        "compte": "Compte",
        "poste": "Poste",
        "fournisseur": "Fournisseur",
        "montant_ttc": "Montant TTC (€)",
    })

    # -------------------------
    # KPI
    # -------------------------
    total = df["montant_ttc"].sum()
    st.metric("Total des dépenses (€)", f"{total:,.2f}")

    # -------------------------
    # Tableau
    # -------------------------
    st.dataframe(
        df_view[[
            "Date",
            "Compte",
            "Poste",
            "Fournisseur",
            "Montant TTC (€)"
        ]],
        use_container_width=True
    )
