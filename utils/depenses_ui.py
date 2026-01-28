import streamlit as st
import pandas as pd


def depenses_ui(supabase):
    st.title("📄 État des dépenses")

    # =========================
    # CHARGEMENT DEPENSES
    # =========================
    dep_res = supabase.table("depenses").select("*").execute()
    df = pd.DataFrame(dep_res.data or [])

    if df.empty:
        st.warning("Aucune dépense trouvée")
        return

    df["date"] = pd.to_datetime(df["date"])
    df["annee"] = df["annee"].astype(int)

    # =========================
    # CHARGEMENT PLAN COMPTABLE
    # =========================
    plan_res = supabase.table("plan_comptable") \
        .select("compte_8, groupe_compte, libelle_groupe") \
        .execute()

    df_plan = pd.DataFrame(plan_res.data or [])

    # =========================
    # JOINTURE DEPENSES ↔ PLAN
    # =========================
    df = df.merge(
        df_plan,
        left_on="compte",
        right_on="compte_8",
        how="left"
    )

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

    groupes = st.sidebar.multiselect(
        "Groupe de compte",
        sorted(df_f["libelle_groupe"].dropna().unique())
    )
    if groupes:
        df_f = df_f[df_f["libelle_groupe"].isin(groupes)]

    fournisseurs = st.sidebar.multiselect(
        "Fournisseur",
        sorted(df_f["fournisseur"].dropna().unique())
    )
    if fournisseurs:
        df_f = df_f[df_f["fournisseur"].isin(fournisseurs)]

    # =========================
    # KPI DEPENSES
    # =========================
    total_dep = df_f["montant_ttc"].sum()
    nb_lignes = len(df_f)
    dep_moy = total_dep / nb_lignes if nb_lignes else 0

    # =========================
    # KPI BUDGET (PAR GROUPE)
    # =========================
    groupes_codes = df_f["groupe_compte"].dropna().unique().tolist()

    bud_res = supabase.table("budgets") \
        .select("budget") \
        .eq("annee", annee) \
        .in_("groupe_compte", groupes_codes) \
        .execute()

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
    # TABLEAU
    # =========================
    st.dataframe(
        df_f[
            [
                "date",
                "compte",
                "poste",
                "libelle_groupe",
                "fournisseur",
                "montant_ttc",
                "commentaire"
            ]
        ].sort_values("date"),
        use_container_width=True
    )

    st.success("État des dépenses chargé correctement ✅")