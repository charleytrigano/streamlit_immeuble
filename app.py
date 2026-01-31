import streamlit as st

# -------------------------
# Connexion Supabase
# -------------------------
from supabase_client import get_supabase_client

# -------------------------
# Import des modules UI
# -------------------------
from appels_fonds_ui import appels_fonds_ui
from plan_comptable_ui import plan_comptable_ui
from depenses_ui import depenses_ui
from budget_ui import budget_ui
from lots_ui import lots_ui
from repartition_lots_ui import repartition_lots_ui
from charges_par_lot_ui import charges_par_lot_ui
from controle_repartition_ui import controle_repartition_ui
from statistiques_ui import statistiques_ui


def main():
    st.set_page_config(page_title="Gestion de l'immeuble", layout="wide")

    st.title("🏢 Gestion de l’immeuble")

    # Connexion Supabase
    supabase = get_supabase_client()
    st.success("✅ Supabase connecté")

    # -------------------------
    # Menu latéral
    # -------------------------
    menu = st.sidebar.radio(
        "Navigation",
        [
            "Appels de fonds",
            "Plan comptable",
            "Dépenses",
            "Budgets",
            "Lots",
            "Répartition des lots",
            "Charges par lot",
            "Contrôle répartition",
            "Statistiques",
        ],
    )

    # -------------------------
    # Routage
    # -------------------------
    if menu == "Appels de fonds":
        appels_fonds_ui(supabase)

    elif menu == "Plan comptable":
        plan_comptable_ui(supabase)

    elif menu == "Dépenses":
        depenses_ui(supabase)

    elif menu == "Budgets":
        budget_ui(supabase)

    elif menu == "Lots":
        lots_ui(supabase)

    elif menu == "Répartition des lots":
        repartition_lots_ui(supabase)

    elif menu == "Charges par lot":
        charges_par_lot_ui(supabase)

    elif menu == "Contrôle répartition":
        controle_repartition_ui(supabase)

    elif menu == "Statistiques":
        statistiques_ui(supabase)


if __name__ == "__main__":
    main()