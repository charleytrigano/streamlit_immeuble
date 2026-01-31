import streamlit as st

from supabase_client import get_supabase_client
from depenses_ui import depenses_ui
from depenses_detail_ui import depenses_detail_ui


# ======================================================
# Configuration Streamlit
# ======================================================
st.set_page_config(
    page_title="Pilotage des charges",
    layout="wide",
)


# ======================================================
# Supabase
# ======================================================
supabase = get_supabase_client()


# ======================================================
# Sidebar – Filtres globaux
# ======================================================
st.sidebar.title("🔎 Filtres globaux")

# ---- Année
annee = st.sidebar.selectbox(
    "Année",
    [2023, 2024, 2025],
    index=2
)

# ---- Chargement valeurs dynamiques depuis la vue DETAIL
# (une seule source de vérité)
data = (
    supabase
    .table("v_depenses_detail")
    .select(
        "groupe_charges, groupe_compte, compte, lot"
    )
    .eq("annee", annee)
    .execute()
)

rows = data.data if data.data else []

def unique_values(col):
    return sorted({r[col] for r in rows if r.get(col) is not None})


# ---- Groupe de charges
groupe_charges = st.sidebar.selectbox(
    "Groupe de charges",
    ["Tous"] + unique_values("groupe_charges")
)

# ---- Groupe de compte
groupe_compte = st.sidebar.selectbox(
    "Groupe de compte",
    ["Tous"] + unique_values("groupe_compte")
)

# ---- Compte
compte = st.sidebar.selectbox(
    "Compte",
    ["Tous"] + unique_values("compte")
)

# ---- Lot
lot = st.sidebar.selectbox(
    "Lot",
    ["Tous"] + unique_values("lot")
)


# ======================================================
# App principale
# ======================================================
def main():
    st.title("📊 Pilotage des charges – Dépenses")

    tabs = st.tabs([
        "📊 Dépenses par groupe de charges",
        "📄 Détail des dépenses",
    ])

    # ----------------------------
    # Onglet 1 – Synthèse
    # ----------------------------
    with tabs[0]:
        depenses_ui(
            supabase=supabase,
            annee=annee,
            groupe_charges=groupe_charges,
            groupe_compte=groupe_compte,
            compte=compte,
            lot=lot,
        )

    # ----------------------------
    # Onglet 2 – Détail
    # ----------------------------
    with tabs[1]:
        depenses_detail_ui(
            supabase=supabase,
            annee=annee,
            groupe_charges=groupe_charges,
            groupe_compte=groupe_compte,
            compte=compte,
            lot=lot,
        )


# ======================================================
# Entrée
# ======================================================
if __name__ == "__main__":
    main()