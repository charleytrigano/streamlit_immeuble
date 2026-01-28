import streamlit as st
import pandas as pd


def depenses_ui(supabase):
    st.title("📄 État des dépenses")

    # =========================
    # Chargement données
    # =========================
    dep = supabase.table("v_depenses_enrichies").select("*").execute().data
    if not dep:
        st.warning("Aucune dépense disponible.")
        return

    df = pd.DataFrame(dep)
    df["montant_ttc"] = pd.to_numeric(df["montant_ttc"], errors="coerce").fillna(0)
    df["annee"] = pd.to_numeric(df["annee"], errors="coerce").astype("Int64")

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
    # Application filtres (LOGIQUE CORRIGÉE)
    # =========================
    df_f = df.copy()

    if annee_sel:
        df_f = df_f[df_f["annee"].isin(annee_sel)]

    # 🔑 PRIORITÉ AU COMPTE
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
    # KPI
    # =========================
    total = df_f["montant_ttc"].sum()
    nb = len(df_f)
    moyenne = total / nb if nb else 0

    c1, c2, c3 = st.columns(3)
    c1.metric("💸 Total dépenses", f"{total:,.2f} €")
    c2.metric("📄 Nombre de lignes", nb)
    c3.metric("📊 Dépense moyenne", f"{moyenne:,.2f} €")

    st.divider()

    # =========================
    # Tableau
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