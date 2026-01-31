import streamlit as st
import pandas as pd


def depenses_ui(supabase, annee):
    st.title("💸 Dépenses par groupe de charges")

    # =========================
    # Chargement depuis la vue agrégée
    # =========================
    resp = (
        supabase
        .table("v_depenses_par_groupe_charges")
        .select("*")
        .eq("annee", annee)
        .execute()
    )

    if not resp.data:
        st.warning("Aucune dépense pour cette année.")
        return

    df = pd.DataFrame(resp.data)

    # =========================
    # Vérification des colonnes
    # =========================
    colonnes_attendues = {"annee", "groupe_charges", "total_depenses"}
    if not colonnes_attendues.issubset(df.columns):
        st.error("Colonnes manquantes dans la vue.")
        st.write("Colonnes disponibles :", list(df.columns))
        return

    # =========================
    # FILTRE GROUPE DE CHARGES
    # =========================
    st.sidebar.subheader("🔎 Filtres")

    groupes = ["Tous"] + sorted(
        df["groupe_charges"]
        .dropna()
        .astype(str)
        .unique()
        .tolist()
    )

    groupe_sel = st.sidebar.selectbox(
        "Groupe de charges",
        groupes
    )

    if groupe_sel != "Tous":
        df = df[df["groupe_charges"].astype(str) == groupe_sel]

    # =========================
    # Affichage tableau
    # =========================
    st.subheader("📊 Dépenses par groupe de charges")

    df_affichage = (
        df
        .rename(columns={
            "groupe_charges": "Groupe de charges",
            "total_depenses": "Total des dépenses (€)"
        })
        .sort_values("Total des dépenses (€)", ascending=False)
    )

    st.dataframe(
        df_affichage,
        use_container_width=True
    )

    # =========================
    # KPI
    # =========================
    total = df["total_depenses"].sum()

    st.metric(
        "Total des dépenses (€)",
        f"{total:,.2f}"
    )