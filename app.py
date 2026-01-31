
import streamlit as st
from supabase_client import get_supabase

from depenses_ui import depenses_ui
from budget_ui import budget_ui
from budget_vs_reel_ui import budget_vs_reel_ui
from plan_comptable_ui import plan_comptable_ui

def main():
    supabase = get_supabase()

    st.sidebar.header("🔎 Filtres globaux")
    annee = st.sidebar.selectbox("Année", [2024, 2025], key="annee_globale")

    onglet = st.sidebar.radio(
        "Navigation",
        ["📄 Dépenses", "💰 Budget", "📊 Budget vs Réel", "📘 Plan comptable"],
        key="nav_principale"
    )

    if onglet == "📄 Dépenses":
        depenses_ui(supabase, annee)

    elif onglet == "💰 Budget":
        budget_ui(supabase, annee)

    elif onglet == "📊 Budget vs Réel":
        budget_vs_reel_ui(supabase, annee)

    elif onglet == "📘 Plan comptable":
        plan_comptable_ui(supabase)

if __name__ == "__main__":
    main()




st.write("📂 CWD =", os.getcwd())
st.write("📁 FICHIERS =", os.listdir("."))
st.write("🐍 sys.path =", sys.path)




st.write("📁 Contenu du dossier courant :")
st.write(os.listdir("."))

st.stop()