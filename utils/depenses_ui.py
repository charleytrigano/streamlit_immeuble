import streamlit as st
import pandas as pd


def depenses_ui(supabase):
    st.title("📄 État des dépenses")

    # =========================
    # 1. Chargement des données
    # =========================

    # Dépenses enrichies avec plan comptable
    depenses_resp = supabase.table("v_depenses_enrichies").select("*").execute()
    depenses = depenses_resp.data

    if not depenses:
        st.warning("Aucune dépense trouvée dans v_depenses_enrichies.")
        return

    df_dep = pd.DataFrame(depenses)

    # Budget vs réel par groupe
    bud_resp = supabase.table("v_budget_vs_reel").select("*").execute()
    budgets = bud_resp.data or []
    df_bud = pd.DataFrame(budgets) if budgets else pd.DataFrame(
        columns=["annee", "groupe_compte", "libelle_groupe", "budget", "reel", "ecart", "taux_budget"]
    )

    # =========================
    # 2. Normalisation
    # =========================

    # Colonnes de base côté dépenses
    df_dep["annee"] = pd.to_numeric(df_dep.get("annee", 0), errors="coerce").fillna(0).astype(int)
    df_dep["montant_ttc"] = pd.to_numeric(df_dep.get("montant_ttc", 0), errors="coerce").fillna(0.0)
    df_dep["lot_id"] = pd.to_numeric(df_dep.get("lot_id", 0), errors="coerce")

    # Budget
    if not df_bud.empty:
        df_bud["annee"] = pd.to_numeric(df_bud.get("annee", 0), errors="coerce").fillna(0).astype(int)
        df_bud["budget"] = pd.to_numeric(df_bud.get("budget", 0), errors="coerce").fillna(0.0)
        df_bud["reel"] = pd.to_numeric(df_bud.get("reel", 0), errors="coerce").fillna(0.0)
        df_bud["ecart"] = pd.to_numeric(df_bud.get("ecart", 0), errors="coerce").fillna(0.0)
        # Si taux_budget absent ou vide, on le recalcule
        if "taux_budget" not in df_bud.columns:
            df_bud["taux_budget"] = df_bud.apply(
                lambda r: (r["reel"] / r["budget"] * 100) if r["budget"] else None,
                axis=1,
            )

    # =========================
    # 3. Filtres (sidebar)
    # =========================

    st.sidebar.header("🎛️ Filtres")

    # Années
    annees = sorted(df_dep["annee"].dropna().unique())
    annee_sel = st.sidebar.multiselect("Année", annees, default=annees)

    # Groupe de compte
    groupes = sorted(df_dep.get("groupe_compte", pd.Series(dtype=str)).dropna().unique())
    if groupes:
        groupe_sel = st.sidebar.multiselect("Groupe de compte", groupes, default=groupes)
    else:
        groupe_sel = []

    # Compte
    comptes = sorted(df_dep.get("compte", pd.Series(dtype=str)).dropna().unique())
    if comptes:
        compte_sel = st.sidebar.multiselect("Compte", comptes, default=comptes)
    else:
        compte_sel = []

    # Fournisseur
    fournisseurs = sorted(df_dep.get("fournisseur", pd.Series(dtype=str)).dropna().unique())
    if fournisseurs:
        fournisseur_sel = st.sidebar.multiselect("Fournisseur", fournisseurs, default=fournisseurs)
    else:
        fournisseur_sel = []

    # Poste
    postes = sorted(df_dep.get("poste", pd.Series(dtype=str)).dropna().unique())
    if postes:
        poste_sel = st.sidebar.multiselect("Poste", postes, default=postes)
    else:
        poste_sel = []

    # Lot
    lots_series = df_dep.get("lot_id", pd.Series(dtype=float)).dropna().unique()
    lots = sorted(lots_series.tolist()) if len(lots_series) > 0 else []
    if lots:
        lot_sel = st.sidebar.multiselect("Lot", lots, default=lots)
    else:
        lot_sel = []

    # =========================
    # 4. Application filtres
    # =========================

    df_f = df_dep.copy()

    if annee_sel:
        df_f = df_f[df_f["annee"].isin(annee_sel)]

    if groupes:
        df_f = df_f[df_f["groupe_compte"].isin(groupe_sel)]

    if comptes:
        df_f = df_f[df_f["compte"].isin(compte_sel)]

    if fournisseurs:
        df_f = df_f[df_f["fournisseur"].isin(fournisseur_sel)]

    if postes:
        df_f = df_f[df_f["poste"].isin(poste_sel)]

    if lots:
        df_f = df_f[df_f["lot_id"].isin(lot_sel)]

    # Si plus rien après filtres
    if df_f.empty:
        st.warning("Aucune dépense pour les filtres choisis.")
        return

    # =========================
    # 5. KPI globaux
    # =========================

    total_depenses = df_f["montant_ttc"].sum()
    nb_lignes = len(df_f)
    depense_moy = df_f["montant_ttc"].mean() if nb_lignes > 0 else 0.0

    # Budget filtré avec cohérence sur annee & groupe_compte
    if not df_bud.empty:
        df_bud_f = df_bud.copy()
        if annee_sel:
            df_bud_f = df_bud_f[df_bud_f["annee"].isin(annee_sel)]
        if groupes:
            df_bud_f = df_bud_f[df_bud_f["groupe_compte"].isin(groupe_sel)]
        total_budget = df_bud_f["budget"].sum()
    else:
        df_bud_f = pd.DataFrame()
        total_budget = 0.0

    ecart_global = total_depenses - total_budget
    taux_budget_global = (total_depenses / total_budget * 100) if total_budget > 0 else None

    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("💸 Total dépenses", f"{total_depenses:,.2f} €")
    c2.metric("📊 Budget", f"{total_budget:,.2f} €")
    c3.metric("📉 Écart", f"{ecart_global:,.2f} €")
    c4.metric("📈 % du budget", f"{taux_budget_global:.2f} %" if taux_budget_global else "—")
    c5.metric("📄 Nombre de lignes", f"{nb_lignes}")

    st.divider()

    # =========================
    # 6. Budget vs Réel par groupe
    # =========================

    st.subheader("📊 Budget vs Réel par groupe")

    if not df_bud_f.empty:
        df_bud_aff = df_bud_f.sort_values(["annee", "groupe_compte"])
        st.dataframe(
            df_bud_aff[
                [
                    "annee",
                    "groupe_compte",
                    "libelle_groupe",
                    "budget",
                    "reel",
                    "ecart",
                    "taux_budget",
                ]
            ],
            use_container_width=True,
        )
    else:
        st.info("Aucun budget correspondant aux filtres (ou vue v_budget_vs_reel vide).")

    st.divider()

    # =========================
    # 7. Détail des dépenses filtrées
    # =========================

    st.subheader("📋 Détail des dépenses")

    colonnes_aff = [
        "date",
        "annee",
        "groupe_compte",
        "libelle_groupe",
        "compte",
        "poste",
        "fournisseur",
        "lot_id",
        "montant_ttc",
        "commentaire",
    ]

    colonnes_aff = [c for c in colonnes_aff if c in df_f.columns]

    df_aff = df_f[colonnes_aff].sort_values("date", ascending=False)

    st.dataframe(df_aff, use_container_width=True)