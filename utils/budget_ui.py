import streamlit as st
import pandas as pd
from utils.budgets_repo import load_budgets, save_budgets


def budget_ui(supabase):
    st.header("💰 Budget annuel")

    annee = st.selectbox(
        "Année budgétaire",
        options=list(range(2020, 2031)),
        index=5  # 2025 par défaut
    )

    df = load_budgets(supabase, annee)

    if df.empty:
        st.warning("Aucun budget pour cette année. Créez-le ci-dessous.")
        df = pd.DataFrame(
            columns=["annee", "compte", "budget", "groupe_compte"]
        )

    edited_df = st.data_editor(
        df,
        num_rows="dynamic",
        use_container_width=True,
        column_config={
            "annee": st.column_config.NumberColumn(disabled=True),
            "budget": st.column_config.NumberColumn(format="%.2f €"),
        },
    )

    if st.button("💾 Enregistrer le budget"):
        edited_df["annee"] = annee
        save_budgets(supabase, edited_df)
        st.success("Budget enregistré avec succès")
        st.rerun()