import streamlit as st
import pandas as pd


def depenses_ui(supabase):
    st.header("📄 État des dépenses")

    # ======================
    # Chargement des données
    # ======================
    res = (
        supabase.table("depenses")
        .select("*")
        .execute()
    )

    df = pd.DataFrame(res.data or [])

    if df.empty:
        st.warning("Aucune dépense")
        return

    # ======================
    # Filtres (SIDEBAR)
    # ======================
    st.sidebar.subheader("Filtres dépenses")

    annee = st.sidebar.selectbox(
        "Année",
        sorted(df["annee"].dropna().unique())
    )

    type_dep = st.sidebar.multiselect(
        "Type",
        sorted(df["type"].dropna().unique())
    )

    df = df[df["annee"] == annee]

    if type_dep:
        df = df[df["type"].isin(type_dep)]

    # ======================
    # Budget (par année)
    # ======================
    bud = (
        supabase.table("budgets")
        .select("budget")
        .eq("annee", annee)
        .execute()
    )

    df_bud = pd.DataFrame(bud.data or [])
    budget_total = df_bud["budget"].sum() if not df_bud.empty else 0

    # ======================
    # KPI
    # ======================
    total_dep = df["montant_ttc"].sum()
    ecart = budget_total - total_dep
    pct_budget = (total_dep / budget_total * 100) if budget_total else 0
    pct_ecart = (ecart / budget_total * 100) if budget_total else 0

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Total dépenses", f"{total_dep:,.2f} €")
    c2.metric("Budget", f"{budget_total:,.2f} €")
    c3.metric("Écart", f"{ecart:,.2f} €")
    c4.metric("% budget consommé", f"{pct_budget:.1f} %")

    # ======================
    # Tableau
    # ======================
    st.dataframe(
        df[
            [
                "depense_id",
                "date",
                "compte",
                "poste",
                "fournisseur",
                "montant_ttc",
                "type",
                "commentaire",
            ]
        ].sort_values("date"),
        use_container_width=True
    )

    # ======================
    # CRUD
    # ======================
    st.subheader("➕ Ajouter une dépense")

    with st.form("add_depense"):
        col1, col2 = st.columns(2)

        with col1:
            date = st.date_input("Date")
            fournisseur = st.text_input("Fournisseur")
            compte = st.text_input("Compte")
            montant = st.number_input("Montant TTC", min_value=0.0)

        with col2:
            poste = st.text_input("Poste")
            type_dep = st.selectbox("Type", ["Charge", "Avoir", "Remboursement"])
            commentaire = st.text_area("Commentaire")

        submit = st.form_submit_button("Ajouter")

        if submit:
            supabase.table("depenses").insert({
                "annee": annee,
                "date": str(date),
                "fournisseur": fournisseur,
                "compte": compte,
                "poste": poste,
                "montant_ttc": montant,
                "type": type_dep,
                "commentaire": commentaire
            }).execute()

            st.success("Dépense ajoutée")
            st.experimental_rerun()