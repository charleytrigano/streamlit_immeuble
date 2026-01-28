import streamlit as st
from supabase import create_client, Client

from utils.depenses_ui import depenses_ui
from utils.budget_ui import budget_ui
from utils.plan_comptable_ui import plan_comptable_ui

from utils.lots_ui import lots_ui

# =========================
# Config & connexion Supabase
# =========================

st.set_page_config(
    page_title="Pilotage des charges",
    page_icon="📊",
    layout="wide",
)

SUPABASE_URL = st.secrets["SUPABASE_URL"]
SUPABASE_KEY = st.secrets["SUPABASE_ANON_KEY"]

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)


def main():
    tabs = st.tabs(["📄 Dépenses", "📑 Budgets", "📘 Plan comptable"])

    with tabs[0]:
        depenses_ui(supabase)

    with tabs[1]:
        budget_ui(supabase)

    with tabs[2]:
        plan_comptable_ui(supabase)

        lots_ui(supabase)

if __name__ == "__main__":
    main()