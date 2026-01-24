import streamlit as st
import pandas as pd


def budget_vs_reel_ui(supabase):
    st.title("📊 Budget vs Réel")

    # -----------------------------
    # Sélection année
    # -----------------------------
    annee = st.selectbox(
        "Année",
        [2023, 2024, 2025, 2026],
        index=0
    )

    # -----------------------------
    # Chargement BUDGET
    # -----------------------------
    budget_resp = (
        supabase
        .table("budgets")  # ✅ CORRECTION ICI
        .select("annee, compte, groupe_compte, budget")
        .eq("annee", annee)
        .execute()
    )

    if not budget_resp.data:
        st.warning("Aucun budget pour cette année.")
        return

    df_budget = pd.DataFrame(budget_resp.data)

    # Sécurité typage
    df_budget["groupe_compte"] = df_budget["groupe_compte"].astype(str)
    df_budget["budget"] = df_budget["budget"].astype(float)

    df_budget = (
        df_budget
        .groupby("groupe_compte", as_index=False)
        .agg(budget=("budget", "sum"))
    )

    # -----------------------------
    # Chargement DÉPENSES
    # -----------------------------
    dep_resp = (
        supabase
        .table("depenses")
        .select("annee, compte, montant_ttc")
        .eq("annee", annee)
        .execute()
    )

    if not dep_resp.data:
        st.warning("Aucune dépense pour cette année.")
        return

    df_dep = pd.DataFrame(dep_resp.data)

    # Sécurité typage
    df_dep["compte"] = df_dep["compte"].astype(str)
    df_dep["montant_ttc"] = df_dep["montant_ttc"].astype(float)

    # -----------------------------
    # Règle GROUPE DE COMPTE
    # -----------------------------
    def compute_groupe(compte: str) -> str:
        if compte in {"6211", "6213", "6222", "6223"}:
            return compte[:4]
        return compte[:3]

    df_dep["groupe_compte"] = df_dep["compte"].apply(compute_groupe)

    df_dep = (
        df_dep
        .groupby("groupe_compte", as_index=False)
        .agg(reel=("montant_ttc", "sum"))
    )

    # -----------------------------
    # Fusion Budget / Réel
    # -----------------------------
    df = pd.merge(
        df_budget,
        df_dep,
        on="groupe_compte",
        how="outer"
    ).fillna(0)

    # -----------------------------
    # KPI
    # -----------------------------
    df["ecart"] = df["budget"] - df["reel"]
    df["ecart_pct"] = df.apply(
        lambda r: (r["ecart"] / r["budget"] * 100) if r["budget"] != 0 else 0,
        axis=1
    )

    # -----------------------------
    # Affichage KPI globaux
    # -----------------------------
    col1, col2, col3, col4 = st.columns(4)

    col1.metric("Budget total (€)", f"{df['budget'].sum():,.2f}")
    col2.metric("Réel (€)", f"{df['reel'].sum():,.2f}")
    col3.metric("Écart (€)", f"{df['ecart'].sum():,.2f}")
    col4.metric(
        "Écart (%)",
        f"{(df['ecart'].sum() / df['budget'].sum() * 100) if df['budget'].sum() != 0 else 0:.2f}%"
    )

    # -----------------------------
    # Tableau final
    # -----------------------------
    df = df.sort_values("groupe_compte")

    st.dataframe(
        df.rename(columns={
            "groupe_compte": "Groupe compte",
            "budget": "Budget (€)",
            "reel": "Réel (€)",
            "ecart": "Écart (€)",
            "ecart_pct": "Écart (%)"
        }),
        use_container_width=True
    )