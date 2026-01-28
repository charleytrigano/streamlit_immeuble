import streamlit as st
from supabase import create_client

from utils.depenses_ui import depenses_ui
from utils.budget_ui import budget_ui
from utils.plan_comptable_ui import plan_comptable_ui

SUPABASE_URL = st.secrets["SUPABASE_URL"]
SUPABASE_ANON_KEY = st.secrets["SUPABASE_ANON_KEY"]

supabase = create_client(SUPABASE_URL, SUPABASE_ANON_KEY)


def main():
    st.set_page_config(page_title="Pilotage des charges", layout="wide")

    page = st.sidebar.radio(
        "Navigation",
        ["Dépenses", "Budgets", "Plan comptable"]
    )

    if page == "Dépenses":
        depenses_ui(supabase)

    elif page == "Budgets":
        budget_ui(supabase)

    elif page == "Plan comptable":
        plan_comptable_ui(supabase)


if __name__ == "__main__":
    main()