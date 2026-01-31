import streamlit as st
import pandas as pd


def euro(x):
    return f"{x:,.2f} €".replace(",", " ").replace(".", ",")


def budget_ui(supabase, annee):
    st.subheader(f"💰 Budget – {annee}")

    # =====================================================
    # BUDGET
    # =====================================================
    bud_resp = (
        supabase
        .table("budgets")
        .select("id, groupe_compte, budget")
        .eq("annee", annee)
        .execute()
    )

    if not bud_resp.data:
        st.warning("Aucun budget pour cette année.")
        return

    df_budget = pd.DataFrame(bud_resp.data)

    # =====================================================
    # PLAN COMPTABLE → groupe_charges
    # =====================================================
    plan_resp = (
        supabase
        .table("plan_comptable")
        .select("groupe_compte, groupe_charges")
        .execute()
    )

    df_plan = pd.DataFrame(plan_resp.data).drop_duplicates("groupe_compte")

    df_budget = df_budget.merge(df_plan, on="groupe_compte", how="left")

    # =====================================================
    # 🔎 FILTRE GROUPE DE CHARGES
    # =====================================================
    groupes = ["Tous"] + sorted(df_budget["groupe_charges"].dropna().unique().tolist())
    groupe_sel = st.selectbox("Groupe de charges", groupes)

    if groupe_sel != "Tous":
        df_budget = df_budget[df_budget["groupe_charges"] == groupe_sel]

    # =====================================================
    # KPI
    # =====================================================
    total_budget = df_budget["budget"].sum()
    st.metric("Budget total", euro(total_budget))

    # =====================================================
    # TABLEAU
    # =====================================================
    st.dataframe(
        df_budget.rename(columns={
            "groupe_charges": "Groupe de charges",
            "groupe_compte": "Groupe de compte",
            "budget": "Budget"
        }).style.format({"Budget": euro}),
        use_container_width=True
    )