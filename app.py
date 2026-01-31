import streamlit as st

from utils.supabase_client import get_supabase_client

# UI modules
from utils.budget_ui import budget_ui
from utils.depenses_ui import depenses_ui
from utils.plan_comptable_ui import plan_comptable_ui
from utils.lots_ui import lots_ui
from utils.repartition_lots_ui import repartition_lots_ui
from utils.charges_par_lot_ui import charges_par_lot_ui
from utils.controle_repartition_ui import controle_repartition_ui
from utils.appels_fonds_trimestre_ui import appels_fonds_trimestre_ui
from utils.statistiques_ui import statistiques_ui


# =============================
# CONFIG STREAMLIT
# =============================
st.set_page_config(
    page_title="Pilotage Immeuble",
    layout="wide"
)


# =============================
# SUPABASE CLIENT
# =============================
@st.cache_resource
def init_supabase():
    return get_supabase_client()


# =============================
# MAIN APP
# =============================
def main():
    st.title("🏢 Pilotage de l’immeuble")

    supabase = init_supabase()

    # Sélecteur d'année global
    annee = st.sidebar.selectbox(
        "📅 Année",
        options=[2024, 2025, 2026],
        index=1
    )

    # Menu principal
    menu = st.sidebar.radio(
        "Navigation",
        [
            "Budgets",
            "Dépenses",
            "Plan comptable",
            "Lots",
            "Répartition par lot",
            "Charges par lot",
            "Contrôle répartition",
            "Appels de fonds trimestriels",
            "Statistiques"
        ]
    )

    # =============================
    # ROUTING UI
    # =============================
    if menu == "Budgets":
        budget_ui(supabase, annee)

    elif menu == "Dépenses":
        depenses_ui(supabase, annee)

    elif menu == "Plan comptable":
        plan_comptable_ui(supabase)

    elif menu == "Lots":
        lots_ui(supabase)

    elif menu == "Répartition par lot":
        repartition_lots_ui(supabase, annee)

    elif menu == "Charges par lot":
        charges_par_lot_ui(supabase, annee)

    elif menu == "Contrôle répartition":
        controle_repartition_ui(supabase, annee)

    elif menu == "Appels de fonds trimestriels":
        appels_fonds_trimestre_ui(supabase, annee)

    elif menu == "Statistiques":
        statistiques_ui(supabase, annee)


# =============================
# ENTRY POINT
# =============================
if __name__ == "__main__":
    main()