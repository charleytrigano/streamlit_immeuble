import streamlit as st
import pandas as pd


def euro(x):
    return f"{x:,.2f} €".replace(",", " ").replace(".", ",")


def budget_vs_reel_ui(supabase, annee):
    st.subheader(f"📊 Budget vs Réel – {annee}")

    # =====================================================
    # RÉEL (vue enrichie)
    # =====================================================
    r_reel = (
        supabase
        .table("v_depenses_enrichies")
        .select(
            "annee, groupe_compte, groupe_charges, montant_ttc"
        )
        .eq("annee", annee)
        .execute()
    )

    if not r_reel.data:
        st.warning("Aucune dépense réelle.")
        return

    df_reel = pd.DataFrame(r_reel.data)

    # =====================================================
    # BUDGET (SANS groupe_charges)
    # =====================================================
    r_budget = (
        supabase
        .table("budget")
        .select(
            "annee, groupe_compte, budget"
        )
        .eq("annee", annee)
        .execute()
    )

    if not r_budget.data:
        st.warning("Aucun budget.")
        return

    df_budget = pd.DataFrame(r_budget.data)

    # =====================================================
    # PLAN COMPTABLE (pour rattacher groupe_charges)
    # =====================================================
    r_plan = (
        supabase
        .table("plan_comptable")
        .select("groupe_compte, groupe_charges")
        .execute()
    )

    df_plan = pd.DataFrame(r_plan.data).drop_duplicates()

    # =====================================================
    # ENRICHISSEMENT DU BUDGET
    # =====================================================
    df_budget = df_budget.merge(
        df_plan,
        on="groupe_compte",
        how="left"
    )

    # =====================================================
    # FILTRE GROUPE DE CHARGES
    # =====================================================
    groupes = (
        ["Tous"]
        + sorted(
            set(df_reel["groupe_charges"].dropna())
            | set(df_budget["groupe_charges"].dropna())
        )
    )

    groupe_sel = st.selectbox(
        "Groupe de charges",
        groupes,
        key="bvr_groupe_charges"
    )

    if groupe_sel != "Tous":
        df_reel = df_reel[df_reel["groupe_charges"] == groupe_sel]
        df_budget = df_budget[df_budget["groupe_charges"] == groupe_sel]

    # =====================================================
    # AGRÉGATIONS
    # =====================================================
    reel_grp = (
        df_reel
        .groupby(["groupe_charges", "groupe_compte"], as_index=False)
        .agg(reel=("montant_ttc", "sum"))
    )

    bud_grp = (
        df_budget
        .groupby(["groupe_charges", "groupe_compte"], as_index=False)
        .agg(budget=("budget", "sum"))
    )

    # =====================================================
    # MERGE FINAL
    # =====================================================
    df = (
        pd.merge(
            bud_grp,
            reel_grp,
            on=["groupe_charges", "groupe_compte"],
            how="outer"
        )
        .fillna(0)
    )

    df["écart"] = df["budget"] - df["reel"]
    df["% écart"] = df.apply(
        lambda r: (r["écart"] / r["budget"] * 100) if r["budget"] != 0 else 0,
        axis=1
    )

    # =====================================================
    # KPI
    # =====================================================
    c1, c2, c3, c4 = st.columns(4)

    c1.metric("Budget", euro(df["budget"].sum()))
    c2.metric("Réel", euro(df["reel"].sum()))
    c3.metric("Écart", euro(df["écart"].sum()))

    pct = (
        df["écart"].sum() / df["budget"].sum() * 100
        if df["budget"].sum() != 0 else 0
    )
    c4.metric("% écart", f"{pct:.2f} %")

    # =====================================================
    # TABLEAU
    # =====================================================
    st.markdown("### 📋 Détail par groupe")

    df_aff = df.copy()
    df_aff["budget"] = df_aff["budget"].apply(euro)
    df_aff["reel"] = df_aff["reel"].apply(euro)
    df_aff["écart"] = df_aff["écart"].apply(euro)
    df_aff["% écart"] = df_aff["% écart"].map(lambda x: f"{x:.2f} %")

    df_aff = df_aff.sort_values(["groupe_charges", "groupe_compte"])

    st.dataframe(df_aff, use_container_width=True)