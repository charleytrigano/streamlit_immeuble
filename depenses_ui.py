import streamlit as st
import pandas as pd


def depenses_ui(supabase, annee):
    st.header("💸 Dépenses par groupe de charges")

    # ======================
    # Chargement des données
    # ======================
    resp = (
        supabase
        .table("v_depenses_enrichies")
        .select("*")
        .eq("annee", annee)
        .execute()
    )

    if not resp.data:
        st.warning("Aucune dépense pour cette année.")
        return

    df = pd.DataFrame(resp.data)

    # ======================
    # Agrégation par groupe
    # ======================
    df_group = (
        df
        .groupby(["groupe_charges", "libelle_groupe"], as_index=False)
        .agg(total_depenses=("montant_ttc", "sum"))
        .sort_values("groupe_charges")
    )

    # ======================
    # Affichage
    # ======================
    st.subheader("📊 Totaux par groupe de charges")

    st.dataframe(
        df_group.rename(columns={
            "groupe_charges": "Groupe",
            "libelle_groupe": "Libellé",
            "total_depenses": "Total dépenses (€)"
        }),
        use_container_width=True
    )

    st.metric(
        "💰 Total général",
        f"{df_group['total_depenses'].sum():,.2f} €"
    )