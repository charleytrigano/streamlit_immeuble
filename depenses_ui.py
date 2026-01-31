import streamlit as st
import pandas as pd


def depenses_ui(supabase):
    st.header("💸 Dépenses")

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
    resp = (
        supabase
        .table("depenses")
        .select("""
            id,
            date_depense,
            libelle,
            montant_ttc,
            compte,
            plan_comptable:compte (
                groupe_compte,
                libelle_groupe
            )
        """)
        .eq("annee", annee)
        .order("date_depense")
        .execute()
    )

    if not resp.data:
        st.info("Aucune dépense pour cette année.")
        return

    df = pd.DataFrame(resp.data)

    # -------------------------
    # Normalisation colonnes jointes
    # -------------------------
    df["groupe_compte"] = df["plan_comptable"].apply(
        lambda x: x["groupe_compte"] if x else None
    )
    df["libelle_groupe"] = df["plan_comptable"].apply(
        lambda x: x["libelle_groupe"] if x else None
    )

    df = df.drop(columns=["plan_comptable"])

    # -------------------------
    # Affichage tableau principal
    # -------------------------
    st.subheader("📋 Liste des dépenses")

    st.dataframe(
        df[[
            "date_depense",
            "libelle",
            "montant_ttc",
            "compte",
            "groupe_compte",
            "libelle_groupe",
        ]].rename(columns={
            "date_depense": "Date",
            "libelle": "Libellé",
            "montant_ttc": "Montant TTC (€)",
            "compte": "Compte",
            "groupe_compte": "Groupe",
            "libelle_groupe": "Libellé groupe",
        }),
        use_container_width=True
    )

    # -------------------------
    # Totaux par groupe
    # -------------------------
    st.subheader("📊 Totaux par groupe de charges")

    df_totaux = (
        df
        .groupby(["groupe_compte", "libelle_groupe"], as_index=False)
        .agg(total=("montant_ttc", "sum"))
        .sort_values("groupe_compte")
    )

    st.dataframe(
        df_totaux.rename(columns={
            "groupe_compte": "Groupe",
            "libelle_groupe": "Libellé groupe",
            "total": "Total (€)",
        }),
        use_container_width=True
    )

    # -------------------------
    # KPI global
    # -------------------------
    total_general = df["montant_ttc"].sum()
    st.metric("💰 Total dépenses", f"{total_general:,.2f} €")