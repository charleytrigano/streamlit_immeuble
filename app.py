import streamlit as st

st.set_page_config(page_title="Immeuble – Pilotage", layout="wide")

st.success("🚀 app.py chargé correctement")

# --- Imports modules UI ---
try:
    from supabase_client import get_supabase_client
    from budget_ui import budget_ui
    from depenses_ui import depenses_ui
    from lots_ui import lots_ui
    from repartition_lots_ui import repartition_lots_ui
    from charges_par_lot_ui import charges_par_lot_ui
    from appels_fonds_trimestre_ui import appels_fonds_trimestriels_ui
    from controle_repartition_ui import controle_repartition_ui
    from plan_comptable_ui import plan_comptable_ui

    st.success("✅ Imports UI OK")
except Exception as e:
    st.error("❌ Erreur d'import des modules UI")
    st.exception(e)
    st.stop()

# --- Supabase ---
supabase = get_supabase_client()

# --- Menu ---
menu = st.sidebar.radio(
    "Navigation",
    [
        "Budget",
        "Dépenses",
        "Lots",
        "Répartition des lots",
        "Charges par lot",
        "Appels de fonds trimestriels",
        "Contrôle répartition",
        "Plan comptable",
    ]
)

# --- Routing ---
if menu == "Budget":
    budget_ui()

elif menu == "Dépenses":
    depenses_ui()

elif menu == "Lots":
    lots_ui()

elif menu == "Répartition des lots":
    repartition_lots_ui()

elif menu == "Charges par lot":
    charges_par_lot_ui()

elif menu == "Appels de fonds trimestriels":
    appels_fonds_trimestriels_ui()

elif menu == "Contrôle répartition":
    controle_repartition_ui()

elif menu == "Plan comptable":
    plan_comptable_ui()
