import streamlit as st
import pandas as pd


def depenses_ui(supabase):
    st.title("📄 État des dépenses")

    # =========================
    # DEPENSES
    # =========================
    dep_res = supabase.table("depenses").select("*").execute()
    df = pd.DataFrame(dep_res.data or [])

    if df.empty:
        st.warning("Aucune dépense")
        return

    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    df["annee"] = df["annee"].astype(int)
    df["compte"] = df["compte"].astype(str).str.strip()

    # =========================
    # PLAN COMPTABLE
    # =========================
    plan_res = supabase.table("plan_comptable") \
        .select("compte_8, groupe_compte, libelle_groupe") \
        .execute()

    df_plan = pd.DataFrame(plan_res.data or [])

    if not df_plan.empty:
        df_plan["compte_8"] = df_plan["compte_8"].astype(str).str.strip()

        df = df.merge(
            df_plan,
            left_on="compte",
            right_on="compte_8",
            how="left"
        )
    else:
        df["groupe_compte"] = None
        df["libelle_groupe"] = None

    # GARANTIE COLONNES
    for col in ["groupe_compte", "libelle_groupe"]:
        if col not in df.columns:
            df[col] = None

    # =========================
    # FILTRES SIDEBAR
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
    nb = len(df_f)
    moy = total_dep / nb if nb else 0

    # =========================
    # KPI BUDGET
    # =========================
    groupes_codes = (
        df_f["groupe_compte"]
        .dropna()
        .astype(str)
        .unique()
        .tolist()
    )

    budget_total = 0

    if groupes_codes:
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
    # KPI AFFICHAGE
    # =========================
    c1, c2, c3, c4, c5 = st.columns(5)

    c1.metric("Total dépenses", f"{total_dep:,.2f} €")
    c2.metric("Budget", f"{budget_total:,.2f} €")
    c3.metric("Écart", f"{ecart:,.2f} €")
    c4.metric("% budget", f"{pct_budget:.1f} %")
    c5.metric("% écart", f"{pct_ecart:.1f} %")

    st.divider()

    # =========================
    # TABLE
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
                "commentaire",
            ]
        ].sort_values("date"),
        use_container_width=True
    )

    st.success("État des dépenses chargé correctement ✅")