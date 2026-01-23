import streamlit as st
import pandas as pd

# ============================
# RÈGLE GROUPE DE COMPTE
# ============================
COMPTES_4_CHIFFRES = {"6211", "6213", "6222", "6223"}


def normalize_compte(compte: str) -> str:
    if compte is None:
        return None
    compte = str(compte)
    if compte[:4] in COMPTES_4_CHIFFRES:
        return compte[:4]
    return compte[:3]


# ============================
# CALCUL BUDGET VS RÉEL
# ============================
def compute_budget_vs_reel(df_budget: pd.DataFrame, df_depenses: pd.DataFrame) -> pd.DataFrame:
    df_budget = df_budget.copy()
    df_depenses = df_depenses.copy()

    df_budget["groupe"] = df_budget["groupe_compte"].astype(str)
    df_depenses["groupe"] = df_depenses["compte"].astype(str).apply(normalize_compte)

    budget_grp = (
        df_budget.groupby("groupe", as_index=False)["budget"].sum()
    )

    depenses_grp = (
        df_depenses.groupby("groupe", as_index=False)["montant_ttc"].sum()
        .rename(columns={"montant_ttc": "reel"})
    )

    df = budget_grp.merge(depenses_grp, on="groupe", how="left").fillna(0)

    df["ecart_eur"] = df["budget"] - df["reel"]
    df["ecart_pct"] = df.apply(
        lambda r: (r["ecart_eur"] / r["budget"] * 100) if r["budget"] else 0,
        axis=1
    )

    return df.sort_values("groupe")


# ============================
# UI STREAMLIT
# ============================
def budget_vs_reel_ui(supabase):
    st.title("📊 Budget vs Réel")

    # ----------------------------
    # ANNÉES DISPONIBLES
    # ----------------------------
    annees_budget = supabase.table("budgets").select("annee").execute().data
    annees_dep = supabase.table("depenses").select("annee").execute().data

    annees = sorted({a["annee"] for a in annees_budget + annees_dep})

    if not annees:
        st.warning("Aucune donnée disponible.")
        return

    annee = st.selectbox("Année", annees, index=len(annees) - 1)

    # ----------------------------
    # BUDGETS (peu de lignes)
    # ----------------------------
    budgets = (
        supabase.table("budgets")
        .select("annee, groupe_compte, budget")
        .eq("annee", annee)
        .execute()
        .data
    )

    if not budgets:
        st.warning("Aucun budget pour cette année.")
        return

    df_budget = pd.DataFrame(budgets)

    # ----------------------------
    # DÉPENSES (⚠️ LIMITÉES)
    # ----------------------------
    depenses = (
        supabase.table("depenses")
        .select("annee, compte, montant_ttc")
        .eq("annee", annee)
        .range(0, 10000)  # ✅ OBLIGATOIRE
        .execute()
        .data
    )

    df_depenses = pd.DataFrame(depenses)

    # ----------------------------
    # CALCUL
    # ----------------------------
    df = compute_budget_vs_reel(df_budget, df_depenses)

    # ----------------------------
    # KPI
    # ----------------------------
    total_budget = df["budget"].sum()
    total_reel = df["reel"].sum()
    total_ecart = total_budget - total_reel

    c1, c2, c3 = st.columns(3)
    c1.metric("Budget total (€)", f"{total_budget:,.2f}")
    c2.metric("Dépenses réelles (€)", f"{total_reel:,.2f}")
    c3.metric("Écart total (€)", f"{total_ecart:,.2f}")

    # ----------------------------
    # TABLEAU FINAL
    # ----------------------------
    st.subheader("Comparaison Budget / Réel")

    st.dataframe(
        df.rename(
            columns={
                "groupe": "Compte",
                "budget": "Budget (€)",
                "reel": "Réel (€)",
                "ecart_eur": "Écart (€)",
                "ecart_pct": "Écart (%)",
            }
        ),
        use_container_width=True
    )