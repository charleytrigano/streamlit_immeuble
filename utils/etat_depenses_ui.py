import streamlit as st
import pandas as pd


def depenses_ui(supabase):
    st.header("📄 État des dépenses")

    # =========================
    # CHARGEMENT DÉPENSES
    # =========================
    dep_res = (
        supabase
        .table("depenses")
        .select(
            "depense_id, annee, date, compte, poste, fournisseur, montant_ttc, type, commentaire"
        )
        .execute()
    )

    df = pd.DataFrame(dep_res.data or [])

    if df.empty:
        st.warning("Aucune dépense enregistrée")
        return

    df["annee"] = df["annee"].astype(int)
    df["montant_ttc"] = df["montant_ttc"].astype(float)
    df["compte"] = df["compte"].astype(str)

    # Groupe de compte = 3 premiers chiffres
    df["groupe_compte"] = df["compte"].str[:3]

    # =========================
    # SIDEBAR — FILTRES
    # =========================
    st.sidebar.subheader("🔎 Filtres dépenses")

    annee = st.sidebar.selectbox(
        "Année",
        sorted(df["annee"].unique())
    )

    comptes = sorted(df["compte"].dropna().unique())
    compte_filtre = st.sidebar.multiselect("Compte", comptes)

    postes = sorted(df["poste"].dropna().unique())
    poste_filtre = st.sidebar.multiselect("Poste", postes)

    fournisseurs = sorted(df["fournisseur"].dropna().unique())
    fournisseur_filtre = st.sidebar.multiselect("Fournisseur", fournisseurs)

    types = sorted(df["type"].dropna().unique())
    type_filtre = st.sidebar.multiselect("Type", types)

    # =========================
    # APPLICATION FILTRES
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
    # KPI — RÉEL
    # =========================
    total_reel = df_f["montant_ttc"].sum()
    nb_lignes = len(df_f)
    dep_moy = total_reel / nb_lignes if nb_lignes else 0

    # =========================
    # CHARGEMENT BUDGET
    # =========================
    groupes_utilises = df_f["groupe_compte"].unique().tolist()

    bud_res = (
        supabase
        .table("budgets")
        .select("annee, groupe_compte, libelle_groupe, budget")
        .eq("annee", annee)
        .in_("groupe_compte", groupes_utilises)
        .execute()
    )

    df_bud = pd.DataFrame(bud_res.data or [])

    budget_total = df_bud["budget"].sum() if not df_bud.empty else 0
    ecart = budget_total - total_reel
    pct_budget = (total_reel / budget_total * 100) if budget_total else 0
    pct_ecart = (ecart / budget_total * 100) if budget_total else 0

    # =========================
    # KPI — AFFICHAGE
    # =========================
    c1, c2, c3, c4, c5 = st.columns(5)

    c1.metric("Total dépenses", f"{total_reel:,.2f} €")
    c2.metric("Budget", f"{budget_total:,.2f} €")
    c3.metric("Écart", f"{ecart:,.2f} €")
    c4.metric("% budget consommé", f"{pct_budget:.1f} %")
    c5.metric("% écart", f"{pct_ecart:.1f} %")

    # =========================
    # TABLEAU DÉPENSES
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