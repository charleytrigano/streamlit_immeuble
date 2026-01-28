import streamlit as st
from supabase import create_client, Client

from utils.depenses_ui import depenses_ui
from utils.budget_ui import budget_ui
from utils.plan_comptable_ui import plan_comptable_ui


@st.cache_resource
def get_supabase() -> Client:
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_ANON_KEY"]  # 🔑 clé correcte
    return create_client(url, key)


def main():
    st.set_page_config(page_title="Pilotage des charges", layout="wide")

    supabase = get_supabase()

    st.title("📊 Pilotage des charges")

    tab_dep, tab_bud, tab_plan = st.tabs(
        ["📄 Dépenses", "📊 Budgets", "📚 Plan comptable"]
    )

    with tab_dep:
        depenses_ui(supabase)

    with tab_bud:
        budget_ui(supabase)

    with tab_plan:
        plan_comptable_ui(supabase)


if __name__ == "__main__":
    main()