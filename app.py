import streamlit as st
from supabase_client import get_supabase_client
from depenses_ui import depenses_ui
from depenses_detail_ui import depenses_detail_ui


st.set_page_config(
    page_title="Pilotage des charges",
    layout="wide",
)

supabase = get_supabase_client()

# ======================================================
# Sidebar – Filtres globaux
# ======================================================
st.sidebar.title("🔎 Filtres globaux")

annee = st.sidebar.selectbox("Année", [2023, 2024, 2025], index=2)

# ======================================================
# Chargement sécurisé des valeurs de filtres
# ======================================================
rows = []

try:
    response = (
        supabase
        .table("v_depenses_detail")
        .select("annee, groupe_charges, groupe_compte, compte")
        .eq("annee", annee)
        .execute()
    )
    rows = response.data or []

except Exception as e:
    st.sidebar.error("Impossible de charger les filtres depuis la base")
    st.sidebar.code(str(e))


def unique_values(col):
    return sorted({r[col] for r in rows if r.get(col) is not None})


groupe_charges = st.sidebar.selectbox(
    "Groupe de charges",
    ["Tous"] + unique_values("groupe_charges")
)

groupe_compte = st.sidebar.selectbox(
    "Groupe de compte",
    ["Tous"] + unique_values("groupe_compte")
)

compte = st.sidebar.selectbox(
    "Compte",
    ["Tous"] + unique_values("compte")
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

    with tabs[0]:
        depenses_ui(
            supabase=supabase,
            annee=annee,
            groupe_charges=groupe_charges,
            groupe_compte=groupe_compte,
            compte=compte,
        )

    with tabs[1]:
        depenses_detail_ui(
            supabase=supabase,
            annee=annee,
            groupe_charges=groupe_charges,
            groupe_compte=groupe_compte,
            compte=compte,
        )


if __name__ == "__main__":
    main()