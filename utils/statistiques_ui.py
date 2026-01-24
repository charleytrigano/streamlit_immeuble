import streamlit as st
import pandas as pd


def statistiques_ui(supabase):
    st.title("📈 Statistiques des dépenses")

    # -----------------------------
    # Chargement données
    # -----------------------------
    resp = (
        supabase
        .table("depenses")
        .select(
            "annee, fournisseur, compte, montant_ttc, type"
        )
        .execute()
    )

    if not resp.data:
        st.warning("Aucune donnée disponible.")
        return

    df = pd.DataFrame(resp.data)

    # Sécurité typage
    df["annee"] = df["annee"].astype(int)
    df["compte"] = df["compte"].astype(str)
    df["montant_ttc"] = df["montant_ttc"].astype(float)
    df["type"] = df["type"].fillna("Charge")

    # -----------------------------
    # Groupe de compte (règle métier)
    # -----------------------------
    def compute_groupe(compte: str) -> str:
        if compte in {"6211", "6213", "6222", "6223"}:
            return compte[:4]
        return compte[:3]

    df["groupe_compte"] = df["compte"].apply(compute_groupe)

    # -----------------------------
    # FILTRES
    # -----------------------------
    col1, col2, col3 = st.columns(3)

    with col1:
        annee = st.multiselect(
            "Année",
            sorted(df["annee"].unique()),
            default=sorted(df["annee"].unique())
        )

    with col2:
        fournisseurs = st.multiselect(
            "Fournisseur",
            sorted(df["fournisseur"].dropna().unique()),
            default=sorted(df["fournisseur"].dropna().unique())
        )

    with col3:
        types = st.multiselect(
            "Type",
            ["Charge", "Remboursement", "Avoir"],
            default=["Charge", "Remboursement", "Avoir"]
        )

    col4, col5 = st.columns(2)

    with col4:
        groupes = st.multiselect(
            "Groupe de compte",
            sorted(df["groupe_compte"].unique()),
            default=sorted(df["groupe_compte"].unique())
        )

    with col5:
        comptes = st.multiselect(
            "Compte",
            sorted(df["compte"].unique()),
            default=sorted(df["compte"].unique())
        )

    # -----------------------------
    # Application filtres
    # -----------------------------
    df_f = df[
        (df["annee"].isin(annee)) &
        (df["fournisseur"].isin(fournisseurs)) &
        (df["type"].isin(types)) &
        (df["groupe_compte"].isin(groupes)) &
        (df["compte"].isin(comptes))
    ]

    if df_f.empty:
        st.warning("Aucune donnée après filtrage.")
        return

    # -----------------------------
    # KPI
    # -----------------------------
    total_depenses = df_f[df_f["type"] == "Charge"]["montant_ttc"].sum()
    total_remb = df_f[df_f["type"] != "Charge"]["montant_ttc"].sum()
    solde = total_depenses + total_remb

    colk1, colk2, colk3, colk4, colk5 = st.columns(5)

    colk1.metric("Total charges (€)", f"{total_depenses:,.2f}")
    colk2.metric("Remboursements (€)", f"{total_remb:,.2f}")
    colk3.metric("Solde net (€)", f"{solde:,.2f}")
    colk4.metric("Nombre de lignes", len(df_f))
    colk5.metric("Dépense moyenne (€)", f"{df_f['montant_ttc'].mean():,.2f}")

    # -----------------------------
    # Tableau
    # -----------------------------
    st.dataframe(
        df_f.sort_values(["annee", "groupe_compte", "compte"]),
        use_container_width=True
    )
