import streamlit as st
import pandas as pd


def depenses_ui(supabase):
    st.header("📋 État des dépenses")

    # =========================
    # Chargement données
    # =========================
    data = (
        supabase.table("depenses")
        .select("*")
        .execute()
        .data
    )

    if not data:
        st.warning("Aucune dépense enregistrée.")
        return

    df = pd.DataFrame(data)

    # Typage propre
    df["annee"] = df["annee"].astype(int)
    df["montant_ttc"] = df["montant_ttc"].astype(float)

    # =========================
    # Filtres
    # =========================
    with st.expander("Filtres", expanded=True):
        col1, col2, col3 = st.columns(3)

        with col1:
            annee = st.selectbox(
                "Année",
                sorted(df["annee"].unique()),
                index=0
            )

        with col2:
            fournisseurs = st.multiselect(
                "Fournisseur",
                sorted(df["fournisseur"].dropna().unique())
            )

        with col3:
            postes = st.multiselect(
                "Poste",
                sorted(df["poste"].dropna().unique())
            )

        types = st.multiselect(
            "Type",
            sorted(df["type"].dropna().unique())
        )

    # =========================
    # Application des filtres
    # =========================
    df_f = df[df["annee"] == annee]

    if fournisseurs:
        df_f = df_f[df_f["fournisseur"].isin(fournisseurs)]

    if postes:
        df_f = df_f[df_f["poste"].isin(postes)]

    if types:
        df_f = df_f[df_f["type"].isin(types)]

    # =========================
    # KPI (APRÈS filtrage)
    # =========================
    total = df_f["montant_ttc"].sum()
    nb = len(df_f)
    moyenne = total / nb if nb > 0 else 0

    col1, col2, col3 = st.columns(3)
    col1.metric("Total dépenses (€)", f"{total:,.2f}")
    col2.metric("Nombre de lignes", nb)
    col3.metric("Dépense moyenne (€)", f"{moyenne:,.2f}")

    # =========================
    # Navigation
    # =========================
    onglet = st.radio(
        "",
        ["📊 Consulter", "➕ Ajouter", "✏️ Modifier", "🗑 Supprimer"],
        horizontal=True
    )

    # =========================
    # Consulter
    # =========================
    if onglet == "📊 Consulter":
        st.dataframe(
            df_f.sort_values("date", ascending=False),
            use_container_width=True
        )