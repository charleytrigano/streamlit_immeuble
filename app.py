import streamlit as st
from config import get_supabase_client

# Modules UI (tous sont à la racine, sans dossier utils)
from budget_ui import budget_ui
from appels_fonds_trimestre_ui import appels_fonds_trimestre_ui
from plan_comptable_ui import plan_comptable_ui
from depenses_ui import depenses_ui
from lots_ui import lots_ui
from repartition_lots_ui import repartition_lots_ui
from charges_par_lot_ui import charges_par_lot_ui
from controle_repartition_ui import controle_repartition_ui


def main():
    st.set_page_config(
        page_title="Gestion de l'immeuble",
        layout="wide",
    )

    st.title("Gestion de l'immeuble")

    # -------------------------
    # Connexion Supabase
    # -------------------------
    with st.spinner("Initialisation Supabase..."):
        supabase = get_supabase_client()

    st.success("✅ Supabase connecté")

    # -------------------------
    # Budget (si tu veux le remettre)
    # -------------------------
    st.markdown("## 📊 Budget")
    budget_ui(supabase)

    # -------------------------
    # Appels de fonds trimestriels
    # -------------------------
    st.markdown("## 💶 Appels de fonds trimestriels")
    appels_fonds_trimestre_ui(supabase)

    # -------------------------
    # Plan comptable – Groupes de charges
    # -------------------------
    st.markdown("## 📚 Plan comptable – Groupes de charges")
    plan_comptable_ui(supabase)

    # -------------------------
    # DÉPENSES
    # -------------------------
    st.markdown("## 💸 Dépenses")
    depenses_ui(supabase)

    # -------------------------
    # Lots
    # -------------------------
    st.markdown("## 🧩 Lots")
    lots_ui(supabase)

    # -------------------------
    # Répartition des lots
    # -------------------------
    st.markdown("## 📐 Répartition des lots")
    repartition_lots_ui(supabase)

    # -------------------------
    # Charges par lot
    # -------------------------
    st.markdown("## 🧾 Charges par lot")
    charges_par_lot_ui(supabase)

    # -------------------------
    # Contrôle répartition
    # -------------------------
    st.markdown("## ✅ Contrôle de répartition")
    controle_repartition_ui(supabase)


if __name__ == "__main__":
    main()