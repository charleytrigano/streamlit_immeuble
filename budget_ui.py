import streamlit as st
import pandas as pd


def budget_ui(supabase, annee):
    st.subheader(f"💰 Budget – {annee}")

    # =========================
    # CHARGEMENT BUDGET
    # =========================
    try:
        res = (
            supabase
            .table("budgets")
            .select("*")
            .eq("annee", annee)
            .execute()
        )
    except Exception as e:
        st.error("Erreur requête Supabase (budgets)")
        st.exception(e)
        return

    if not res.data:
        st.warning("Aucun budget pour cette année.")
        return

    df = pd.DataFrame(res.data)

    # =========================
    # KPI
    # =========================
    total_budget = df["budget"].sum()

    col1, = st.columns(1)
    col1.metric("Budget total", f"{total_budget:,.2f} €".replace(",", " "))

    # =========================
    # TABLEAU
    # =========================
    st.markdown("### 📋 Détail du budget")

    st.dataframe(
        df.sort_values("groupe_compte"),
        use_container_width=True
    )