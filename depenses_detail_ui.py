import streamlit as st
import pandas as pd


def depenses_detail_ui(supabase, annee):
    st.title("📄 Détail des dépenses")

    # =========================
    # Chargement des données
    # =========================
    response = (
        supabase
        .table("v_depenses_detail")
        .select("*")
        .eq("annee", annee)
        .execute()
    )

    if not response.data:
        st.warning("Aucune dépense trouvée pour cette année.")
        return

    df = pd.DataFrame(response.data)

    # =========================
    # Filtres
    # =========================
    st.subheader("🔎 Filtres")

    groupes = ["Tous"] + sorted(df["groupe_charges"].dropna().unique().tolist())
    groupe_sel = st.selectbox("Groupe de charges", groupes)

    if groupe_sel != "Tous":
        df = df[df["groupe_charges"] == groupe_sel]

    # =========================
    # Tableau détail
    # =========================
    st.subheader("📋 Dépenses détaillées")

    df_affichage = df[
        [
            "date",
            "compte",
            "libelle_compte",
            "poste",
            "groupe_charges",
            "montant_ttc",
        ]
    ].copy()

    df_affichage["date"] = pd.to_datetime(df_affichage["date"])
    df_affichage = df_affichage.sort_values("date")

    st.dataframe(
        df_affichage,
        use_container_width=True,
        hide_index=True,
    )

    # =========================
    # Total
    # =========================
    total = df_affichage["montant_ttc"].sum()

    st.metric(
        label="💰 Total des dépenses affichées",
        value=f"{total:,.2f} €".replace(",", " ")
    )