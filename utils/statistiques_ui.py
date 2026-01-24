import streamlit as st
import pandas as pd


def statistiques_ui(supabase):
    st.title("📈 Statistiques des dépenses")

    # =============================
    # Chargement données
    # =============================
    resp = (
        supabase
        .table("depenses")
        .select("annee, fournisseur, compte, montant_ttc, type")
        .execute()
    )

    if not resp.data:
        st.warning("Aucune donnée disponible.")
        return

    df = pd.DataFrame(resp.data)

    # =============================
    # NORMALISATION (clé)
    # =============================
    df["annee"] = pd.to_numeric(df["annee"], errors="coerce").astype("Int64")
    df["compte"] = df["compte"].astype(str)
    df["montant_ttc"] = pd.to_numeric(df["montant_ttc"], errors="coerce").fillna(0)

    # Fournisseur
    df["fournisseur"] = df["fournisseur"].fillna("Non renseigné")

    # Type (normalisation réelle)
    df["type"] = (
        df["type"]
        .fillna("Charge")
        .str.strip()
        .str.capitalize()
    )

    # =============================
    # Groupe de compte (règle métier)
    # =============================
    def compute_groupe(compte: str) -> str:
        if compte[:4] in {"6211", "6213", "6222", "6223"}:
            return compte[:4]
        return compte[:3]

    df["groupe_compte"] = df["compte"].apply(compute_groupe)

    # =============================
    # FILTRES (dynamiques & sûrs)
    # =============================
    col1, col2, col3 = st.columns(3)

    with col1:
        annees = st.multiselect(
            "Année",
            options=sorted(df["annee"].dropna().unique()),
            default=sorted(df["annee"].dropna().unique())
        )

    with col2:
        fournisseurs = st.multiselect(
            "Fournisseur",
            options=sorted(df["fournisseur"].unique()),
            default=sorted(df["fournisseur"].unique())
        )

    with col3:
        types = st.multiselect(
            "Type",
            options=sorted(df["type"].unique()),
            default=sorted(df["type"].unique())
        )

    col4, col5 = st.columns(2)

    with col4:
        groupes = st.multiselect(
            "Groupe de compte",
            options=sorted(df["groupe_compte"].unique()),
            default=sorted(df["groupe_compte"].unique())
        )

    with col5:
        comptes = st.multiselect(
            "Compte",
            options=sorted(df["compte"].unique()),
            default=sorted(df["compte"].unique())
        )

    # =============================
    # APPLICATION DES FILTRES
    # =============================
    df_f = df.copy()

    if annees:
        df_f = df_f[df_f["annee"].isin(annees)]
    if fournisseurs:
        df_f = df_f[df_f["fournisseur"].isin(fournisseurs)]
    if types:
        df_f = df_f[df_f["type"].isin(types)]
    if groupes:
        df_f = df_f[df_f["groupe_compte"].isin(groupes)]
    if comptes:
        df_f = df_f[df_f["compte"].isin(comptes)]

    if df_f.empty:
        st.warning("Aucune donnée après application des filtres.")
        return

    # =============================
    # KPI
    # =============================
    charges = df_f[df_f["type"] == "Charge"]["montant_ttc"].sum()
    autres = df_f[df_f["type"] != "Charge"]["montant_ttc"].sum()
    solde = charges + autres

    k1, k2, k3, k4, k5 = st.columns(5)

    k1.metric("Total charges (€)", f"{charges:,.2f}")
    k2.metric("Avoirs / Remb. (€)", f"{autres:,.2f}")
    k3.metric("Solde net (€)", f"{solde:,.2f}")
    k4.metric("Nombre de lignes", len(df_f))
    k5.metric("Montant moyen (€)", f"{df_f['montant_ttc'].mean():,.2f}")

    # =============================
    # TABLEAU
    # =============================
    st.dataframe(
        df_f.sort_values(["annee", "groupe_compte", "compte"]),
        use_container_width=True
    )