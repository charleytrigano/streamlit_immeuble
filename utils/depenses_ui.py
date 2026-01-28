import streamlit as st
import pandas as pd
from datetime import date


def depenses_ui(supabase):
    st.title("📄 État des dépenses")

    # =========================
    # CHARGEMENT DES DONNÉES
    # =========================
    res = supabase.table("depenses").select("*").execute()
    df = pd.DataFrame(res.data or [])

    if df.empty:
        st.warning("Aucune dépense trouvée")
        return

    # =========================
    # NORMALISATION
    # =========================
    df["date"] = pd.to_datetime(df["date"])
    df["annee"] = df["annee"].astype(int)

    # =========================
    # SIDEBAR – FILTRES
    # =========================
    st.sidebar.header("Filtres")

    annee = st.sidebar.selectbox(
        "Année",
        sorted(df["annee"].unique()),
        index=len(df["annee"].unique()) - 1
    )

    df_f = df[df["annee"] == annee]

    comptes = st.sidebar.multiselect(
        "Compte",
        sorted(df_f["compte"].dropna().unique())
    )
    if comptes:
        df_f = df_f[df_f["compte"].isin(comptes)]

    postes = st.sidebar.multiselect(
        "Poste",
        sorted(df_f["poste"].dropna().unique())
    )
    if postes:
        df_f = df_f[df_f["poste"].isin(postes)]

    fournisseurs = st.sidebar.multiselect(
        "Fournisseur",
        sorted(df_f["fournisseur"].dropna().unique())
    )
    if fournisseurs:
        df_f = df_f[df_f["fournisseur"].isin(fournisseurs)]

    date_min = st.sidebar.date_input(
        "Date début",
        df_f["date"].min().date()
    )
    date_max = st.sidebar.date_input(
        "Date fin",
        df_f["date"].max().date()
    )

    df_f = df_f[
        (df_f["date"] >= pd.to_datetime(date_min)) &
        (df_f["date"] <= pd.to_datetime(date_max))
    ]

    # =========================
    # KPI – DÉPENSES
    # =========================
    total_dep = df_f["montant_ttc"].sum()
    nb_lignes = len(df_f)
    dep_moy = total_dep / nb_lignes if nb_lignes else 0

    # =========================
    # KPI – BUDGET
    # =========================
    groupes = df_f["groupe_compte"].dropna().unique().tolist()

    bud_res = (
        supabase
        .table("budgets")
        .select("budget")
        .eq("annee", annee)
        .in_("groupe_compte", groupes)
        .execute()
    )

    df_bud = pd.DataFrame(bud_res.data or [])

    budget_total = df_bud["budget"].sum() if not df_bud.empty else 0
    ecart = budget_total - total_dep
    pct_budget = (total_dep / budget_total * 100) if budget_total else 0
    pct_ecart = (ecart / budget_total * 100) if budget_total else 0

    # =========================
    # AFFICHAGE KPI
    # =========================
    c1, c2, c3, c4, c5 = st.columns(5)

    c1.metric("Total dépenses", f"{total_dep:,.2f} €")
    c2.metric("Budget", f"{budget_total:,.2f} €")
    c3.metric("Écart", f"{ecart:,.2f} €")
    c4.metric("% budget consommé", f"{pct_budget:.1f} %")
    c5.metric("% écart", f"{pct_ecart:.1f} %")

    st.divider()

    # =========================
    # TABLEAU DÉPENSES
    # =========================
    st.dataframe(
        df_f[
            [
                "date",
                "compte",
                "poste",
                "fournisseur",
                "montant_ttc",
                "type",
                "commentaire"
            ]
        ].sort_values("date"),
        use_container_width=True
    )

    st.success("Module dépenses chargé correctement ✅")