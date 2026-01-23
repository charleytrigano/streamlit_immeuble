import streamlit as st
import pandas as pd


def budget_vs_reel_ui(supabase):
    st.header("📊 Budget vs Réel")

    # =========================
    # Sélection année
    # =========================
    annees = (
        supabase.table("budgets")
        .select("annee")
        .execute()
        .data
    )

    annees = sorted({a["annee"] for a in annees})

    if not annees:
        st.warning("Aucune année budgétaire disponible.")
        return

    annee = st.selectbox("Année", annees)

    # =========================
    # Chargement budgets
    # =========================
    df_budget = (
        supabase.table("budgets")
        .select("annee, compte, budget")
        .eq("annee", annee)
        .execute()
        .data
    )

    df_budget = pd.DataFrame(df_budget)

    if df_budget.empty:
        st.warning("Aucun budget pour cette année.")
        return

    df_budget["groupe"] = df_budget["compte"].astype(str).str[:3]
    df_budget = (
        df_budget
        .groupby("groupe", as_index=False)["budget"]
        .sum()
    )

    # =========================
    # Chargement dépenses
    # =========================
    df_dep = (
        supabase.table("depenses")
        .select("annee, compte, montant_ttc")
        .eq("annee", annee)
        .execute()
        .data
    )

    df_dep = pd.DataFrame(df_dep)

    if df_dep.empty:
        df_dep = pd.DataFrame(columns=["groupe", "reel"])

    else:
        df_dep["compte"] = df_dep["compte"].astype(str)

        df_dep["groupe"] = df_dep["compte"].apply(
            lambda x: x[:3] if len(x) >= 4 else x
        )

        df_dep = (
            df_dep
            .groupby("groupe", as_index=False)["montant_ttc"]
            .sum()
            .rename(columns={"montant_ttc": "reel"})
        )

    # =========================
    # Fusion Budget / Réel
    # =========================
    df = pd.merge(
        df_budget,
        df_dep,
        on="groupe",
        how="left"
    )

    df["reel"] = df["reel"].fillna(0)
    df["ecart"] = df["budget"] - df["reel"]
    df["ecart_pct"] = df.apply(
        lambda r: (r["ecart"] / r["budget"] * 100)
        if r["budget"] != 0 else None,
        axis=1
    )

    df = df.rename(columns={"groupe": "compte"})

    # =========================
    # KPI
    # =========================
    col1, col2, col3 = st.columns(3)

    col1.metric("Budget total (€)", f"{df['budget'].sum():,.2f}")
    col2.metric("Réel total (€)", f"{df['reel'].sum():,.2f}")
    col3.metric("Écart global (€)", f"{df['ecart'].sum():,.2f}")

    # =========================
    # Tableau final
    # =========================
    st.dataframe(
        df[["compte", "budget", "reel", "ecart", "ecart_pct"]],
        use_container_width=True
    )