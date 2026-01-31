# =========================
# SIDEBAR – FILTRES GLOBAUX
# =========================
st.sidebar.title("🔎 Filtres globaux")

annee = st.sidebar.selectbox(
    "Année",
    options=[2023, 2024, 2025, 2026],
    index=2
)

# =========================
# ONGLET DÉPENSES
# =========================
with tab_dep:
    try:
        from depenses_ui import depenses_ui
        depenses_ui(supabase, annee)   # 👈 ICI la correction
    except Exception as e:
        st.error("❌ Erreur module Dépenses")
        st.exception(e)