import streamlit as st
from supabase import create_client

from utils.depenses_ui import depenses_ui
from utils.budget_ui import budget_ui
from utils.budget_vs_reel_ui import budget_vs_reel_ui
from utils.statistiques_ui import statistiques_ui
from utils.controle_repartition_ui import controle_repartition_ui
from utils.plan_comptable_ui import plan_comptable_ui

st.set_page_config(page_title="Pilotage des charges", layout="wide")

@st.cache_resource
def get_supabase():
    return create_client(
        st.secrets["SUPABASE_URL"],
        st.secrets["SUPABASE_ANON_KEY"]
    )

def main():
    supabase = get_supabase()

    st.sidebar.title("Navigation")

    page = st.sidebar.radio(
        "Aller à",
        [
            "📄 État des dépenses",
            "💰 Budget",
            "📊 Budget vs Réel",
            "📈 Statistiques",
            "✅ Contrôle répartition",
            "📚 Plan comptable"
        ]
    )

    if page == "📄 État des dépenses":
        depenses_ui(supabase)

    elif page == "💰 Budgets":
        budget_ui(supabase)

    elif page == "📊 Budget vs Réel":
        budget_vs_reel_ui(supabase)

    elif page == "📈 Statistiques":
        statistiques_ui(supabase)

    elif page == "✅ Contrôle répartition":
        controle_repartition_ui(supabase)

    elif page == "📚 Plan comptable":
        plan_comptable_ui(supabase)

if __name__ == "__main__":
    main()
