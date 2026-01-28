import streamlit as st
import pandas as pd

# =========================
# FORMAT €
# =========================
def euro(x):
    return f"{x:,.2f} €".replace(",", " ").replace(".", ",")

# =========================
# UI
# =========================
def budget_vs_reel_ui(supabase, annee):
    st.header("📊 Budget vs Réel")

    # =========================
    # CHARGEMENT DES DONNÉES
    # =========================
    dep = supabase.table("depenses").select(
        "annee, compte, montant_ttc"
    ).eq("annee", annee).execute().data

    bud = supabase.table("budgets").select(
        "annee, groupe_compte, libelle_groupe, budget"
    ).eq("annee", annee).execute().data

    plan = supabase.table("plan_comptable").select(
        "compte_8, groupe_compte, libelle_groupe"
    ).execute().data

    df_dep = pd.DataFrame(dep)
    df_bud = pd.DataFrame(bud)
    df_plan = pd.DataFrame(plan)

    if df_dep.empty and df_bud.empty:
        st.warning("Aucune donnée pour cette année.")
        return

    # =========================
    # RATTACHEMENT DES DÉPENSES AU GROUPE
    # =========================
    if not df_dep.empty:
        df_dep = df_dep.merge(
            df_plan,
            left_on="compte",
            right_on="compte_8",
            how="left"
        )

    # =========================
    # AGRÉGATION DU RÉEL PAR GROUPE
    # =========================
    reel_groupe = (
        df_dep
        .groupby(["groupe_compte", "libelle_groupe"], as_index=False)
        .agg(reel=("montant_ttc", "sum"))
        if not df_dep.empty
        else pd.DataFrame(columns=["groupe_compte", "libelle_groupe", "reel"])
    )

    # =========================
    # AGRÉGATION DU BUDGET PAR GROUPE
    # =========================
    budget_groupe = (
        df_bud
        .groupby(["groupe_compte", "libelle_groupe"], as_index=False)
        .agg(budget=("budget", "sum"))
        if not df_bud.empty
        else pd.DataFrame(columns=["groupe_compte", "libelle_groupe", "budget"])
    )

    # =========================
    # MERGE BUDGET VS RÉEL
    # =========================
    synthese = budget_groupe.merge(
        reel_groupe,
        on=["groupe_compte", "libelle_groupe"],
        how="outer"
    ).fillna(0)

    synthese["écart"] = synthese["reel"] - synthese["budget"]
    synthese["écart_%"] = synthese.apply(
        lambda r: (r["écart"] / r["budget"] * 100) if r["budget"] != 0 else 0,
        axis=1
    )

    # =========================
    # KPI
    # =========================
    col1, col2, col3, col4 = st.columns(4)

    col1.metric("Budget total", euro(synthese["budget"].sum()))
    col2.metric("Réel total", euro(synthese["reel"].sum()))
    col3.metric("Écart", euro(synthese["écart"].sum()))
    col4.metric(
        "Écart %",
        f"{(synthese['écart'].sum() / synthese['budget'].sum() * 100):.2f} %"
        if synthese["budget"].sum() != 0 else "0 %"
    )

    # =========================
    # TABLEAU 1 — BUDGET VS RÉEL PAR GROUPE
    # =========================
    st.subheader("📘 Budget vs Réel par groupe de comptes")

    st.dataframe(
        synthese.sort_values("groupe_compte").rename(columns={
            "groupe_compte": "Groupe",
            "libelle_groupe": "Libellé",
            "budget": "Budget (€)",
            "reel": "Réel (€)",
            "écart": "Écart (€)",
            "écart_%": "Écart (%)"
        }),
        use_container_width=True
    )

    # =========================
    # TABLEAU 2 — DÉTAIL DU RÉEL
    # =========================
    st.subheader("📄 Détail du réel (dépenses)")

    if df_dep.empty:
        st.info("Aucune dépense pour cette année.")
        return

    detail = (
        df_dep
        .groupby(
            ["groupe_compte", "libelle_groupe", "compte"],
            as_index=False
        )
        .agg(reel=("montant_ttc", "sum"))
        .sort_values(["groupe_compte", "compte"])
    )

    st.dataframe(
        detail.rename(columns={
            "groupe_compte": "Groupe",
            "libelle_groupe": "Libellé groupe",
            "compte": "Compte",
            "reel": "Réel (€)"
        }),
        use_container_width=True
    )