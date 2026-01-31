import streamlit as st
import pandas as pd


def euro(x):
    if x is None:
        return "0,00 €"
    return f"{x:,.2f} €".replace(",", " ").replace(".", ",")


def budget_vs_reel_ui(supabase, annee):
    st.header(f"📊 Budget vs Réel – {annee}")

    # ======================================================
    # BUDGET
    # ======================================================
    bud_resp = (
        supabase
        .table("budgets")
        .select("groupe_compte, budget")
        .eq("annee", annee)
        .execute()
    )

    if not bud_resp.data:
        st.warning("Aucun budget pour cette année.")
        return

    df_bud = pd.DataFrame(bud_resp.data)

    # ======================================================
    # PLAN COMPTABLE (groupe_charges)
    # ======================================================
    plan_resp = (
        supabase
        .table("plan_comptable")
        .select("groupe_compte, groupe_charges")
        .execute()
    )

    df_plan = pd.DataFrame(plan_resp.data).drop_duplicates()

    # ======================================================
    # BUDGET → GROUPE DE CHARGES
    # ======================================================
    df_bud = df_bud.merge(
        df_plan,
        on="groupe_compte",
        how="left"
    )

    df_bud_group = (
        df_bud
        .groupby("groupe_charges", as_index=False)
        .agg(budget=("budget", "sum"))
    )

    # ======================================================
    # RÉEL (DÉPENSES)
    # ======================================================
    dep_resp = (
        supabase
        .table("depenses")
        .select("depense_id, compte, montant_ttc, date, poste")
        .eq("annee", annee)
        .execute()
    )

    if not dep_resp.data:
        st.warning("Aucune dépense pour cette année.")
        return

    df_dep = pd.DataFrame(dep_resp.data)

    df_dep = df_dep.merge(
        supabase
        .table("plan_comptable")
        .select("compte_8, groupe_charges")
        .execute()
        .data,
        left_on="compte",
        right_on="compte_8",
        how="left"
    )

    df_reel_group = (
        df_dep
        .groupby("groupe_charges", as_index=False)
        .agg(reel=("montant_ttc", "sum"))
    )

    # ======================================================
    # BUDGET VS RÉEL
    # ======================================================
    df_bvr = df_bud_group.merge(
        df_reel_group,
        on="groupe_charges",
        how="left"
    ).fillna(0)

    df_bvr["ecart"] = df_bvr["budget"] - df_bvr["reel"]
    df_bvr["ecart_pct"] = df_bvr.apply(
        lambda r: (r["ecart"] / r["budget"] * 100)
        if r["budget"] != 0 else 0,
        axis=1
    )

    # ======================================================
    # KPI
    # ======================================================
    st.subheader("📊 Indicateurs globaux")

    total_budget = df_bvr["budget"].sum()
    total_reel = df_bvr["reel"].sum()
    ecart = total_budget - total_reel
    pct = (ecart / total_budget * 100) if total_budget else 0

    k1, k2, k3, k4 = st.columns(4)
    k1.metric("Budget total", euro(total_budget))
    k2.metric("Réel total", euro(total_reel))
    k3.metric("Écart", euro(ecart))
    k4.metric("Écart %", f"{pct:.2f} %")

    # ======================================================
    # TABLEAU SYNTHÈSE
    # ======================================================
    st.subheader("📘 Synthèse par groupe de charges")

    df_view = df_bvr.copy()
    df_view["budget"] = df_view["budget"].apply(euro)
    df_view["reel"] = df_view["reel"].apply(euro)
    df_view["ecart"] = df_view["ecart"].apply(euro)
    df_view["ecart_pct"] = df_view["ecart_pct"].round(2).astype(str) + " %"

    st.dataframe(
        df_view.rename(columns={
            "groupe_charges": "Groupe de charges",
            "budget": "Budget",
            "reel": "Réel",
            "ecart": "Écart",
            "ecart_pct": "Écart %"
        }),
        use_container_width=True
    )

    # ======================================================
    # DÉTAIL DU RÉEL
    # ======================================================
    st.subheader("📋 Détail des dépenses")

    st.dataframe(
        df_dep[[
            "date",
            "compte",
            "poste",
            "montant_ttc",
            "groupe_charges"
        ]].sort_values("date"),
        use_container_width=True
    )