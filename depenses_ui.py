import streamlit as st
import pandas as pd


def depenses_ui(supabase, annee):
    st.title("💸 Dépenses par groupe de charges")

    # =========================
    # Chargement depuis la VUE
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
    # Sécurité minimale
    # =========================
    required_cols = {"groupe_charges", "montant_ttc"}
    if not required_cols.issubset(df.columns):
        st.error(
            "La vue v_depenses_par_groupe_charges ne contient pas les colonnes attendues : "
            + ", ".join(required_cols)
        )
        st.dataframe(df.head())
        return

    # =========================
    # Filtre groupe de charges
    # =========================
    groupes = ["Tous"] + sorted(df["groupe_charges"].dropna().unique().tolist())
    groupe_sel = st.selectbox("Groupe de charges", groupes)

    if groupe_sel != "Tous":
        df = df[df["groupe_charges"] == groupe_sel]

    # =========================
    # Tableau
    # =========================
    st.subheader("📊 Dépenses")

    df_view = (
        df
        .groupby("groupe_charges", as_index=False)
        .agg(
            total_depenses=("montant_ttc", "sum")
        )
        .sort_values("total_depenses", ascending=False)
    )

    st.dataframe(
        df_view,
        use_container_width=True
    )

    # =========================
    # KPI
    # =========================
    total = df_view["total_depenses"].sum()

    st.metric(
        "Total dépenses (€)",
        f"{total:,.2f}"
    )