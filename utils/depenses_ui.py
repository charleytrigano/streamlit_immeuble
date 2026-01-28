import streamlit as st
import pandas as pd


def depenses_ui(supabase):
    st.title("📄 État des dépenses")

    # =========================
    # CHARGEMENT DES DONNÉES
    # =========================
    dep = supabase.table("depenses").select("*").execute()
    bud = supabase.table("budgets").select("*").execute()
    plan = supabase.table("plan_comptable").select("*").execute()

    if not dep.data:
        st.warning("Aucune dépense enregistrée.")
        return

    df_dep = pd.DataFrame(dep.data)
    df_bud = pd.DataFrame(bud.data) if bud.data else pd.DataFrame()
    df_plan = pd.DataFrame(plan.data)

    # =========================
    # ENRICHISSEMENT
    # =========================
    df_dep["date"] = pd.to_datetime(df_dep["date"], errors="coerce")
    df_dep["annee"] = df_dep["date"].dt.year

    df_dep = df_dep.merge(
        df_plan[["compte_8", "groupe_compte", "libelle_groupe"]],
        left_on="compte",
        right_on="compte_8",
        how="left"
    )

    # =========================
    # SIDEBAR – FILTRES
    # =========================
    st.sidebar.header("🎛️ Filtres")

    annee_sel = st.sidebar.multiselect(
        "Année",
        sorted(df_dep["annee"].dropna().unique()),
        default=sorted(df_dep["annee"].dropna().unique())
    )

    groupe_sel = st.sidebar.multiselect(
        "Groupe de compte",
        sorted(df_dep["groupe_compte"].dropna().astype(str).unique())
    )

    compte_sel = st.sidebar.multiselect(
        "Compte",
        sorted(df_dep["compte"].dropna().unique())
    )

    fournisseur_sel = st.sidebar.multiselect(
        "Fournisseur",
        sorted(df_dep["fournisseur"].dropna().unique())
    )

    poste_sel = st.sidebar.multiselect(
        "Poste",
        sorted(df_dep["poste"].dropna().unique())
    )

    type_sel = st.sidebar.multiselect(
        "Type",
        sorted(df_dep["type"].dropna().unique())
    )

    # =========================
    # APPLICATION DES FILTRES
    # =========================
    df_f = df_dep.copy()

    if annee_sel:
        df_f = df_f[df_f["annee"].isin(annee_sel)]

    if groupe_sel:
        df_f = df_f[df_f["groupe_compte"].astype(str).isin(groupe_sel)]

    if compte_sel:
        df_f = df_f[df_f["compte"].isin(compte_sel)]

    if fournisseur_sel:
        df_f = df_f[df_f["fournisseur"].isin(fournisseur_sel)]

    if poste_sel:
        df_f = df_f[df_f["poste"].isin(poste_sel)]

    if type_sel:
        df_f = df_f[df_f["type"].isin(type_sel)]

    # =========================
    # KPI – DÉPENSES
    # =========================
    total_dep = df_f["montant_ttc"].sum()
    nb_lignes = len(df_f)
    dep_moy = total_dep / nb_lignes if nb_lignes > 0 else 0

    # =========================
    # KPI – BUDGET (LOGIQUE CORRECTE)
    # =========================
    budget_total = 0.0
    ecart_montant = 0.0
    ecart_pct = 0.0

    if not df_bud.empty:
        df_bf = df_bud.copy()

        if annee_sel:
            df_bf = df_bf[df_bf["annee"].isin(annee_sel)]

        # PRIORITÉ AU COMPTE
        if compte_sel and "compte" in df_bf.columns:
            df_bf = df_bf[df_bf["compte"].isin(compte_sel)]

        # SINON GROUPE
        elif groupe_sel:
            df_bf["groupe_compte"] = df_bf["groupe_compte"].astype(str)
            df_bf = df_bf[df_bf["groupe_compte"].isin(groupe_sel)]

        # SINON GROUPES PRÉSENTS DANS LES DÉPENSES
        else:
            groupes_dep = (
                df_f["groupe_compte"]
                .dropna()
                .astype(str)
                .unique()
                .tolist()
            )
            df_bf["groupe_compte"] = df_bf["groupe_compte"].astype(str)
            df_bf = df_bf[df_bf["groupe_compte"].isin(groupes_dep)]

        budget_total = df_bf["budget"].sum()

        if budget_total > 0:
            ecart_montant = budget_total - total_dep
            ecart_pct = (ecart_montant / budget_total) * 100

    # =========================
    # AFFICHAGE KPI
    # =========================
    c1, c2, c3, c4, c5 = st.columns(5)

    c1.metric("💰 Dépenses", f"{total_dep:,.2f} €")
    c2.metric("📊 Budget", f"{budget_total:,.2f} €")
    c3.metric("📉 Écart (€)", f"{ecart_montant:,.2f} €")
    c4.metric("📐 Écart (%)", f"{ecart_pct:,.1f} %")
    c5.metric("🧾 Nb lignes", nb_lignes)

    # =========================
    # TABLEAU
    # =========================
    if df_f.empty:
        st.warning("Aucune dépense pour les filtres choisis.")
        return

    st.dataframe(
        df_f[
            [
                "date",
                "annee",
                "groupe_compte",
                "libelle_groupe",
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