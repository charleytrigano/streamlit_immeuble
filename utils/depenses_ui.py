import streamlit as st
import pandas as pd


def depenses_ui(supabase):
    st.title("📄 État des dépenses")

    # =========================
    # Chargement données DEPENSES
    # =========================
    dep = supabase.table("v_depenses_enrichies").select("*").execute().data
    if not dep:
        st.warning("Aucune dépense disponible.")
        return

    df = pd.DataFrame(dep)
    df["montant_ttc"] = pd.to_numeric(df["montant_ttc"], errors="coerce").fillna(0)
    df["annee"] = pd.to_numeric(df["annee"], errors="coerce").astype("Int64")

    # =========================
    # Chargement données BUDGETS
    # =========================
    try:
        bud = supabase.table("budgets").select("*").execute().data
        df_bud = pd.DataFrame(bud) if bud else pd.DataFrame()
    except Exception:
        df_bud = pd.DataFrame()

    if not df_bud.empty:
        df_bud["annee"] = pd.to_numeric(df_bud["annee"], errors="coerce").astype("Int64")
        df_bud["budget"] = pd.to_numeric(df_bud["budget"], errors="coerce").fillna(0)
        # sécurité texte
        df_bud["groupe_compte"] = df_bud["groupe_compte"].astype(str)
    # =========================
    # Sidebar – filtres
    # =========================
    st.sidebar.header("🎛️ Filtres")

    annees = sorted(df["annee"].dropna().unique())
    annee_sel = st.sidebar.multiselect("Année", annees, default=annees)

    groupes = sorted(df["groupe_compte"].dropna().unique())
    groupe_sel = st.sidebar.multiselect("Groupe de compte", groupes, default=[])

    comptes = sorted(df["compte"].dropna().unique())
    compte_sel = st.sidebar.multiselect("Compte", comptes, default=[])

    fournisseurs = sorted(df["fournisseur"].dropna().unique())
    fournisseur_sel = st.sidebar.multiselect("Fournisseur", fournisseurs, default=[])

    postes = sorted(df["poste"].dropna().unique())
    poste_sel = st.sidebar.multiselect("Poste", postes, default=[])

    lots = sorted(df["lot_id"].dropna().unique())
    lot_sel = st.sidebar.multiselect("Lot", lots, default=[])

    # =========================
    # Application filtres (LOGIQUE HIÉRARCHIQUE)
    # =========================
    df_f = df.copy()

    if annee_sel:
        df_f = df_f[df_f["annee"].isin(annee_sel)]

    # 🔑 PRIORITÉ AU COMPTE : si des comptes sont choisis,
    # on ignore le filtre groupe_compte.
    if compte_sel:
        df_f = df_f[df_f["compte"].isin(compte_sel)]
    elif groupe_sel:
        df_f = df_f[df_f["groupe_compte"].isin(groupe_sel)]

    if poste_sel:
        df_f = df_f[df_f["poste"].isin(poste_sel)]

    if fournisseur_sel:
        df_f = df_f[df_f["fournisseur"].isin(fournisseur_sel)]

    if lot_sel:
        df_f = df_f[df_f["lot_id"].isin(lot_sel)]

    # =========================
    # Sécurité UX
    # =========================
    if df_f.empty:
        st.warning("Aucune dépense pour les filtres choisis.")
        return

    # =========================
    # KPI – Réalisé, Budget, Écarts
    # =========================
    total_dep = df_f["montant_ttc"].sum()
    nb = len(df_f)
    moyenne = total_dep / nb if nb else 0

    # ---- Calcul du budget pour le même périmètre ----
    budget_total = 0.0
    ecart_montant = 0.0
    ecart_pct = 0.0

    if not df_bud.empty:
        # on prend seulement les années visibles
        df_bud_f = df_bud.copy()
        if annee_sel:
            df_bud_f = df_bud_f[df_bud_f["annee"].isin(annee_sel)]

        # on se cale sur les groupes réellement présents dans les dépenses filtrées
        groupes_dep = df_f["groupe_compte"].dropna().astype(str).unique()
        if len(groupes_dep) > 0:
            df_bud_f = df_bud_f[df_bud_f["groupe_compte"].isin(groupes_dep)]

        budget_total = df_bud_f["budget"].sum()

        if budget_total > 0:
            ecart_montant = budget_total - total_dep
            ecart_pct = (ecart_montant / budget_total) * 100
        else:
            ecart_montant = 0.0
            ecart_pct = 0.0

    # =========================
    # Affichage KPI
    # =========================
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("💸 Total dépenses", f"{total_dep:,.2f} €")
    c2.metric("📊 Budget total", f"{budget_total:,.2f} €")
    c3.metric("🔀 Écart (Budget - Réel)", f"{ecart_montant:,.2f} €")
    c4.metric("📈 Écart / Budget", f"{ecart_pct:,.2f} %")

    c5, c6 = st.columns(2)
    c5.metric("📄 Nombre de lignes", nb)
    c6.metric("💶 Dépense moyenne", f"{moyenne:,.2f} €")

    st.divider()

    # =========================
    # Tableau des dépenses
    # =========================
    colonnes = [
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
    colonnes = [c for c in colonnes if c in df_f.columns]

    st.dataframe(
        df_f[colonnes].sort_values("date", ascending=False),
        use_container_width=True,
    )