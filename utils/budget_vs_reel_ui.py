import streamlit as st
import pandas as pd


def euro(x):
    return f"{x:,.2f} €".replace(",", " ").replace(".", ",")


def budget_vs_reel_ui(supabase, annee):
    st.header("📊 Budget vs Réel")

    # ======================================================
    # CHARGEMENT DES DONNÉES
    # ======================================================
    dep = (
        supabase
        .table("depenses")
        .select("*")
        .eq("annee", annee)
        .execute()
        .data
    )

    bud = (
        supabase
        .table("budgets")
        .select("*")
        .eq("annee", annee)
        .execute()
        .data
    )

    plan = (
        supabase
        .table("plan_comptable")
        .select("*")
        .execute()
        .data
    )

    df_dep = pd.DataFrame(dep)
    df_bud = pd.DataFrame(bud)
    df_plan = pd.DataFrame(plan)

    if df_dep.empty:
        st.warning("Aucune dépense pour cette année.")
        return

    if df_bud.empty:
        st.warning("Aucun budget pour cette année.")
        return

    # ======================================================
    # NORMALISATION
    # ======================================================
    df_dep["montant_ttc"] = pd.to_numeric(df_dep["montant_ttc"], errors="coerce").fillna(0)
    df_bud["budget"] = pd.to_numeric(df_bud["budget"], errors="coerce").fillna(0)

    # ======================================================
    # RATTACHEMENT PLAN COMPTABLE AUX DÉPENSES
    # ======================================================
    df_dep = df_dep.merge(
        df_plan[["compte_8", "libelle", "groupe_compte"]],
        left_on="compte",
        right_on="compte_8",
        how="left"
    )

    # ======================================================
    # AGRÉGATION RÉEL PAR GROUPE DE COMPTES
    # ======================================================
    reel_par_groupe = (
        df_dep
        .groupby("groupe_compte", dropna=False)
        .agg(reel=("montant_ttc", "sum"))
        .reset_index()
    )

    # ======================================================
    # AGRÉGATION BUDGET PAR GROUPE
    # ======================================================
    budget_par_groupe = (
        df_bud
        .groupby(["groupe_compte", "libelle_groupe"], dropna=False)
        .agg(budget=("budget", "sum"))
        .reset_index()
    )

    # ======================================================
    # TABLEAU BUDGET VS RÉEL
    # ======================================================
    df_bvr = budget_par_groupe.merge(
        reel_par_groupe,
        on="groupe_compte",
        how="left"
    )

    df_bvr["reel"] = df_bvr["reel"].fillna(0)
    df_bvr["ecart"] = df_bvr["reel"] - df_bvr["budget"]
    df_bvr["ecart_pct"] = df_bvr.apply(
        lambda r: (r["ecart"] / r["budget"] * 100) if r["budget"] != 0 else 0,
        axis=1
    )

    # ======================================================
    # KPI GLOBAUX
    # ======================================================
    col1, col2, col3, col4 = st.columns(4)

    total_budget = df_bvr["budget"].sum()
    total_reel = df_bvr["reel"].sum()
    total_ecart = total_reel - total_budget
    pct_ecart = (total_ecart / total_budget * 100) if total_budget != 0 else 0

    col1.metric("💰 Budget total", euro(total_budget))
    col2.metric("💸 Réel total", euro(total_reel))
    col3.metric("📉 Écart", euro(total_ecart))
    col4.metric("📊 Écart %", f"{pct_ecart:.2f} %")

    # ======================================================
    # TABLEAU SYNTHÈSE
    # ======================================================
    st.subheader("📋 Synthèse Budget vs Réel par groupe")

    st.dataframe(
        df_bvr[[
            "groupe_compte",
            "libelle_groupe",
            "budget",
            "reel",
            "ecart",
            "ecart_pct"
        ]].rename(columns={
            "groupe_compte": "Groupe",
            "libelle_groupe": "Libellé groupe",
            "budget": "Budget (€)",
            "reel": "Réel (€)",
            "ecart": "Écart (€)",
            "ecart_pct": "Écart (%)"
        }).sort_values("groupe"),
        use_container_width=True
    )

    # ======================================================
    # DÉTAIL DU RÉEL PAR POSTE
    # ======================================================
    st.subheader("🔍 Détail du réel par poste")

    postes = (
        df_dep["poste"]
        .dropna()
        .sort_values()
        .unique()
        .tolist()
    )

    if not postes:
        st.info("Aucun poste renseigné dans les dépenses.")
        return

    poste_sel = st.selectbox(
        "Sélectionne un poste",
        options=postes
    )

    df_poste = df_dep[df_dep["poste"] == poste_sel]

    total_poste = df_poste["montant_ttc"].sum()

    st.metric(
        f"Total réel — {poste_sel}",
        euro(total_poste)
    )

    # ======================================================
    # TABLEAU DÉTAILLÉ DES DÉPENSES
    # ======================================================
    df_detail = df_poste[[
        "date",
        "fournisseur",
        "poste",
        "compte",
        "libelle",
        "montant_ttc",
        "commentaire",
        "facture_url"
    ]].sort_values("date")

    df_detail = df_detail.rename(columns={
        "date": "Date",
        "fournisseur": "Fournisseur",
        "poste": "Poste",
        "compte": "Compte",
        "libelle": "Libellé du compte",
        "montant_ttc": "Montant TTC (€)",
        "commentaire": "Commentaire",
        "facture_url": "Facture"
    })

    st.dataframe(
        df_detail,
        use_container_width=True
    )