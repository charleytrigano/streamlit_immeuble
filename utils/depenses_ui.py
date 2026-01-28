import streamlit as st
import pandas as pd


def depenses_ui(supabase):
    st.header("📄 État des dépenses")

    # =========================
    # Chargement données
    # =========================
    res = (
        supabase
        .table("depenses")
        .select(
            "depense_id, annee, date, compte, poste, fournisseur, montant_ttc, type, commentaire"
        )
        .execute()
    )

    df = pd.DataFrame(res.data or [])

    if df.empty:
        st.warning("Aucune dépense enregistrée")
        return

    # Sécurités
    df["annee"] = df["annee"].astype(int)
    df["montant_ttc"] = df["montant_ttc"].astype(float)

    # =========================
    # SIDEBAR — FILTRES
    # =========================
    st.sidebar.subheader("🔎 Filtres dépenses")

    # Année
    annee = st.sidebar.selectbox(
        "Année",
        sorted(df["annee"].unique())
    )

    # Compte
    comptes = sorted(df["compte"].dropna().unique())
    compte_filtre = st.sidebar.multiselect("Compte", comptes)

    # Poste
    postes = sorted(df["poste"].dropna().unique())
    poste_filtre = st.sidebar.multiselect("Poste", postes)

    # Fournisseur
    fournisseurs = sorted(df["fournisseur"].dropna().unique())
    fournisseur_filtre = st.sidebar.multiselect("Fournisseur", fournisseurs)

    # Type
    types = sorted(df["type"].dropna().unique())
    type_filtre = st.sidebar.multiselect("Type", types)

    # =========================
    # Application filtres
    # =========================
    df_f = df[df["annee"] == annee]

    if compte_filtre:
        df_f = df_f[df_f["compte"].isin(compte_filtre)]

    if poste_filtre:
        df_f = df_f[df_f["poste"].isin(poste_filtre)]

    if fournisseur_filtre:
        df_f = df_f[df_f["fournisseur"].isin(fournisseur_filtre)]

    if type_filtre:
        df_f = df_f[df_f["type"].isin(type_filtre)]

    # =========================
    # KPI (basés sur filtres)
    # =========================
    total_dep = df_f["montant_ttc"].sum()
    nb_lignes = len(df_f)
    dep_moy = total_dep / nb_lignes if nb_lignes else 0

    c1, c2, c3 = st.columns(3)
    c1.metric("Total dépenses", f"{total_dep:,.2f} €")
    c2.metric("Nombre de lignes", nb_lignes)
    c3.metric("Dépense moyenne", f"{dep_moy:,.2f} €")

    # =========================
    # TABLEAU
    # =========================
    st.dataframe(
        df_f.sort_values("date")[
            [
                "date",
                "compte",
                "poste",
                "fournisseur",
                "montant_ttc",
                "type",
                "commentaire",
            ]
        ],
        use_container_width=True
    )