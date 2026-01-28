import streamlit as st
from supabase import create_client
from utils.depenses_ui import depenses_ui

# -----------------------------
# CONFIG STREAMLIT
# -----------------------------
st.set_page_config(
    page_title="Immeuble – Pilotage",
    layout="wide"
)

# -----------------------------
# SUPABASE
# -----------------------------
SUPABASE_URL = st.secrets["SUPABASE_URL"]
SUPABASE_ANON_KEY = st.secrets["SUPABASE_ANON_KEY"]

supabase = create_client(SUPABASE_URL, SUPABASE_ANON_KEY)

# -----------------------------
# MAIN
# -----------------------------
def main():
    st.sidebar.title("Navigation")
    page = st.sidebar.radio(
        "Menu",
        ["Dépenses"]
    )

    if page == "Dépenses":
        depenses_ui(supabase)


if __name__ == "__main__":
    main()