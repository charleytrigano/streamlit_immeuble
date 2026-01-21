import streamlit as st
import pandas as pd

from utils.supabase_client import get_supabase
from utils.budgets_repo import load_budgets, save_budgets
from utils.depenses_repo import load_depenses
from utils.budget_vs_reel_ui import budget_vs_reel_ui

# ======================
# CONFIG
# ======================
st.set_page_config(
    page_title="Pilotage des charges de l’immeuble",
    layout="wide",
)

supabase = get_supabase()

# ======================
# SIDEBAR
# ======================
st.sidebar.title("📊 Navigation")

page = st.sidebar.radio(
    "Aller à",
    [
        "📈 État des dépenses",
        "💰 Budget",
        "📊 Budget vs Réel",
    ],
)

# ======================
# PAGE : DÉPENSES
# ======================
if page == "📈 État des dépenses":
    st.title("📈 Pilotage des charges de l’immeuble")

    annee = st.selectbox(
        "Année",
        options=list(range(2020, 2031)),
        index=5
    )

    df = load_depenses(supabase, annee)

    if df.empty:
        st.info("Aucune dépense pour cette année.")
        st.stop()

    col1, col2 = st.columns(2)
    col1.metric("Total dépenses (€)", f"{df['montant_ttc'].sum():,.2f}")
    col2.metric("Nombre de lignes", len(df))

    st.divider()
    st.subheader("Détail des dépenses")

    st.dataframe(
        df[
            [
                "date",
                "compte",
                "poste",
                "fournisseur",
                "montant_ttc",
                "piece_id",
                "pdf_url",
            ]
        ],
        use_container_width=True,
    )

# ======================
# PAGE : BUDGET
# ======================
elif page == "💰 Budget":
    st.title("💰 Budget annuel")

    annee = st.selectbox(
        "Année budgétaire",
        options=list(range(2020, 2031)),
        index=5
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

# ======================
# PAGE : BUDGET VS RÉEL
# ======================
elif page == "📊 Budget vs Réel":
    budget_vs_reel_ui(supabase)