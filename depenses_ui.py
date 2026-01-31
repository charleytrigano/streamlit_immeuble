import streamlit as st
import pandas as pd


def depenses_ui(supabase, annee):
    st.title("💸 Dépenses par groupe de charges")

    # =========================
    # Chargement depuis la vue
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
    # Vérification minimale
    # =========================
    colonnes_attendues = {"groupe_charges", "montant_ttc"}
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
    # Agrégation
    # =========================
    df_group = (
        df
        .groupby("groupe_charges", as_index=False)
        .agg(total_depenses=("montant_ttc", "sum"))
        .sort_values("total_depenses", ascending=False)
    )

    # =========================
    # Affichage
    # =========================
    st.subheader("📊 Dépenses par groupe de charges")

    st.dataframe(
        df_group,
        use_container_width=True
    )

    # =========================
    # KPI
    # =========================
    total = df_group["total_depenses"].sum()

    st.metric(
        "Total des dépenses (€)",
        f"{total:,.2f}"
    )