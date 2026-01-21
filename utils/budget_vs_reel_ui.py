import streamlit as st
from utils.budgets_repo import load_budgets
from utils.depenses_repo import load_depenses
from utils.budget_vs_reel_repo import compute_budget_vs_reel


def budget_vs_reel_ui(supabase):
    st.title("📊 Budget vs Réel – Analyse")

    annee = st.selectbox(
        "Année",
        options=list(range(2020, 2031)),
        index=5
    )

    df_bud = load_budgets(supabase, annee)
    df_dep = load_depenses(supabase, annee)

    if df_bud.empty:
        st.warning("Aucun budget pour cette année.")
        return

    st.write("Colonnes dépenses :", df_dep.columns.tolist())
    st.dataframe(df_dep.head())
    st.stop()

    df_comp = compute_budget_vs_reel(df_bud, df_dep)

    if df_comp.empty:
        st.info("Aucune dépense rattachée.")
        return

    # KPI globaux
    col1, col2, col3 = st.columns(3)
    col1.metric("Budget total (€)", f"{df_comp['budget'].sum():,.2f}")
    col2.metric("Réel total (€)", f"{df_comp['reel'].sum():,.2f}")
    col3.metric("Écart total (€)", f"{df_comp['ecart_eur'].sum():,.2f}")

    st.divider()

    # Filtres
    groupes = ["Tous"] + sorted(
        [g for g in df_comp["groupe_compte"].dropna().unique()]
    )

    groupe_sel = st.selectbox("Groupe de comptes", groupes)

    if groupe_sel != "Tous":
        df_comp = df_comp[df_comp["groupe_compte"] == groupe_sel]

    st.subheader("Comparaison Budget / Réel")

    st.dataframe(
        df_comp[
            [
                "groupe_compte",
                "compte_budget",
                "budget",
                "reel",
                "ecart_eur",
                "ecart_pct",
            ]
        ],
        use_container_width=True,
    )
