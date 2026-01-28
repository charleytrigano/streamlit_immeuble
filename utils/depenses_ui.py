import streamlit as st
import pandas as pd


def depenses_ui(supabase):
    st.title("📄 État des dépenses")

    # =========================
    # 1. Chargement des données
    # =========================

    depenses = supabase.table("v_depenses_enrichies").select("*").execute().data
    budgets = supabase.table("v_budget_vs_reel").select("*").execute().data

    if not depenses:
        st.warning("Aucune dépense trouvée")
        return

    df_dep = pd.DataFrame(depenses)
    df_budget = pd.DataFrame(budgets)

    # =========================
    # 2. Normalisation
    # =========================

    df_dep["annee"] = df_dep["annee"].astype(int)
    df_dep["montant_ttc"] = pd.to_numeric(df_dep["montant_ttc"], errors="coerce").fillna(0)

    if not df_budget.empty:
        df_budget["annee"] = df_budget["annee"].astype(int)
        df_budget["budget"] = pd.to_numeric(df_budget["budget"], errors="coerce").fillna(0)
        df_budget["reel"] = pd.to_numeric(df_budget["reel"], errors="coerce").fillna(0)
        df_budget["ecart"] = pd.to_numeric(df_budget["ecart"], errors="coerce").fillna(0)

    # =========================
    # 3. Filtres (SIDEBAR)
    # =========================

    st.sidebar.header("🎛️ Filtres")

    annees = sorted(df_dep["annee"].dropna().unique())
    annee_sel = st.sidebar.multiselect(
        "Année", annees, default=annees
    )

    groupes = sorted(df_dep["groupe_compte"].dropna().unique())
    groupe_sel = st.sidebar.multiselect(
        "Groupe de charges", groupes, default=groupes
    )

    comptes = sorted(df_dep["compte"].dropna().unique())
    compte_sel = st.sidebar.multiselect(
        "Compte comptable", comptes, default=comptes
    )

    lots = sorted(df_dep["lot_id"].dropna().unique())
    lot_sel = st.sidebar.multiselect(
        "Lot", lots, default=lots
    )

    # =========================
    # 4. Application filtres
    # =========================

    df_f = df_dep[
        (df_dep["annee"].isin(annee_sel)) &
        (df_dep["groupe_compte"].isin(groupe_sel)) &
        (df_dep["compte"].isin(compte_sel)) &
        (df_dep["lot_id"].isin(lot_sel))
    ]

    # =========================
    # 5. KPI GLOBAUX
    # =========================

    total_depenses = df_f["montant_ttc"].sum()
    nb_lignes = len(df_f)
    depense_moy = df_f["montant_ttc"].mean() if nb_lignes > 0 else 0

    total_budget = df_budget[
        (df_budget["annee"].isin(annee_sel)) &
        (df_budget["groupe_compte"].isin(groupe_sel))
    ]["budget"].sum()

    ecart_global = total_depenses - total_budget
    taux_budget = (
        (total_depenses / total_budget) * 100
        if total_budget > 0 else None
    )

    c1, c2, c3, c4, c5 = st.columns(5)

    c1.metric("💰 Dépenses réelles", f"{total_depenses:,.2f} €")
    c2.metric("📊 Budget", f"{total_budget:,.2f} €")
    c3.metric("📉 Écart", f"{ecart_global:,.2f} €")
    c4.metric("📈 % budget", f"{taux_budget:.2f} %" if taux_budget else "—")
    c5.metric("📄 Lignes", nb_lignes)

    st.divider()

    # =========================
    # 6. Tableau BUDGET vs RÉEL par groupe
    # =========================

    st.subheader("📊 Budget vs Réel par groupe")

    df_kpi = df_budget[
        (df_budget["annee"].isin(annee_sel)) &
        (df_budget["groupe_compte"].isin(groupe_sel))
    ].copy()

    df_kpi = df_kpi.sort_values("groupe_compte")

    st.dataframe(
        df_kpi[[
            "annee",
            "groupe_compte",
            "libelle_groupe",
            "budget",
            "reel",
            "ecart",
            "taux_budget"
        ]],
        use_container_width=True
    )

    st.divider()

    # =========================
    # 7. Tableau DÉTAIL DES DÉPENSES
    # =========================

    st.subheader("📋 Détail des dépenses")

    df_aff = df_f[[
        "date",
        "annee",
        "groupe_compte",
        "libelle_groupe",
        "compte",
        "poste",
        "fournisseur",
        "montant_ttc",
        "lot_id",
        "commentaire"
    ]].sort_values("date", ascending=False)

    st.dataframe(df_aff, use_container_width=True)