import streamlit as st
import pandas as pd


def euro(x):
    if x is None:
        return "0,00 €"
    return f"{x:,.2f} €".replace(",", " ").replace(".", ",")


def budget_vs_reel_ui(supabase, annee):
    st.subheader(f"📊 Budget vs Réel – {annee}")

    # =====================================================
    # BUDGET (sans groupe_charges)
    # =====================================================
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

    df_budget = pd.DataFrame(bud_resp.data)

    # =====================================================
    # PLAN COMPTABLE (pour groupe_charges)
    # =====================================================
    plan_resp = (
        supabase
        .table("plan_comptable")
        .select("groupe_compte, groupe_charges")
        .execute()
    )

    df_plan = pd.DataFrame(plan_resp.data).drop_duplicates("groupe_compte")

    # enrichissement budget → groupe_charges
    df_budget = df_budget.merge(
        df_plan,
        on="groupe_compte",
        how="left"
    )

    # =====================================================
    # RÉEL (vue enrichie)
    # =====================================================
    dep_resp = (
        supabase
        .table("v_depenses_enrichies")
        .select("groupe_compte, groupe_charges, montant_ttc")
        .eq("annee", annee)
        .execute()
    )

    if not dep_resp.data:
        st.warning("Aucune dépense pour cette année.")
        return

    df_dep = pd.DataFrame(dep_resp.data)

    # =====================================================
    # AGRÉGATIONS
    # =====================================================
    bud_grp = (
        df_budget
        .groupby(["groupe_charges", "groupe_compte"], as_index=False)
        .agg(budget=("budget", "sum"))
    )

    dep_grp = (
        df_dep
        .groupby(["groupe_charges", "groupe_compte"], as_index=False)
        .agg(reel=("montant_ttc", "sum"))
    )

    df = bud_grp.merge(
        dep_grp,
        on=["groupe_charges", "groupe_compte"],
        how="left"
    )

    df["reel"] = df["reel"].fillna(0)
    df["ecart"] = df["budget"] - df["reel"]
    df["ecart_pct"] = df.apply(
        lambda r: (r["ecart"] / r["budget"] * 100) if r["budget"] else 0,
        axis=1
    )

    # =====================================================
    # KPI
    # =====================================================
    budget_total = df["budget"].sum()
    reel_total = df["reel"].sum()
    ecart_total = budget_total - reel_total

    c1, c2, c3 = st.columns(3)
    c1.metric("Budget total", euro(budget_total))
    c2.metric("Réel total", euro(reel_total))
    c3.metric("Écart", euro(ecart_total))

    # =====================================================
    # TABLEAU FINAL
    # =====================================================
    st.dataframe(
        df.sort_values(["groupe_charges", "groupe_compte"]).rename(columns={
            "groupe_charges": "Groupe de charges",
            "groupe_compte": "Groupe de compte",
            "budget": "Budget",
            "reel": "Réel",
            "ecart": "Écart",
            "ecart_pct": "Écart %"
        }).style.format({
            "Budget": euro,
            "Réel": euro,
            "Écart": euro,
            "Écart %": "{:.2f} %"
        }),
        use_container_width=True
    )