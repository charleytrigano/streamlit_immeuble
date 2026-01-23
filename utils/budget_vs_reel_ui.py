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
        df_budget
        .groupby("groupe", as_index=False)["budget"]
        .sum()
        .rename(columns={"budget": "budget"})
    )

    depenses_grp = (
        df_depenses
        .groupby("groupe", as_index=False)["montant_ttc"]
        .sum()
        .rename(columns={"montant_ttc": "reel"})
    )

    df = budget_grp.merge(depenses_grp, on="groupe", how="outer").fillna(0)

    df["ecart_eur"] = df["budget"] - df["reel"]
    df["ecart_pct"] = df.apply(
        lambda r: (r["ecart_eur"] / r["budget"] * 100) if r["budget"] != 0 else 0,
        axis=1
    )

    df = df.sort_values("groupe")

    return df


# ============================
# UI STREAMLIT
# ============================
def budget_vs_reel_ui(supabase):
    st.title("📊 Budget vs Réel")

    # ----------------------------
    # ANNÉE
    # ----------------------------
    annees_budget = (
        supabase.table("budgets")
        .select("annee")
        .execute()
        .data
    )

    annees_depenses = (
        supabase.table("depenses")
        .select("annee")
        .execute()
        .data
    )

    annees = sorted(
        set([a["annee"] for a in annees_budget] + [a["annee"] for a in annees_depenses])
    )

    if not annees:
        st.warning("Aucune donnée budget ou dépense.")
        return

    annee = st.selectbox("Année", annees, index=len(annees) - 1)

    # ----------------------------
    # DONNÉES
    # ----------------------------
    budgets = (
        supabase.table("budgets")
        .select("annee, groupe_compte, budget")
        .eq("annee", annee)
        .execute()
        .data
    )

    depenses = (
        supabase.table("depenses")
        .select("annee, compte, montant_ttc")
        .eq("annee", annee)
        .execute()
        .data
    )

    if not budgets:
        st.warning("Aucun budget pour cette année.")
        return

    df_budget = pd.DataFrame(budgets)
    df_depenses = pd.DataFrame(depenses)

    df_comp = compute_budget_vs_reel(df_budget, df_depenses)

    # ----------------------------
    # KPI
    # ----------------------------
    total_budget = df_comp["budget"].sum()
    total_reel = df_comp["reel"].sum()
    total_ecart = total_budget - total_reel

    c1, c2, c3 = st.columns(3)
    c1.metric("Budget total (€)", f"{total_budget:,.2f}")
    c2.metric("Dépenses réelles (€)", f"{total_reel:,.2f}")
    c3.metric("Écart total (€)", f"{total_ecart:,.2f}")

    # ----------------------------
    # TABLEAU FINAL
    # ----------------------------
    st.subheader("Comparaison par groupe de compte")

    df_aff = df_comp.copy()
    df_aff["budget"] = df_aff["budget"].round(2)
    df_aff["reel"] = df_aff["reel"].round(2)
    df_aff["ecart_eur"] = df_aff["ecart_eur"].round(2)
    df_aff["ecart_pct"] = df_aff["ecart_pct"].round(1)

    st.dataframe(
        df_aff.rename(
            columns={
                "groupe": "Compte / Groupe",
                "budget": "Budget (€)",
                "reel": "Réel (€)",
                "ecart_eur": "Écart (€)",
                "ecart_pct": "Écart (%)",
            }
        ),
        use_container_width=True
    )