import streamlit as st
import pandas as pd
from supabase import create_client

# =========================
# CONFIG
# =========================
st.set_page_config(
    page_title="Pilotage des charges",
    layout="wide"
)

# =========================
# SUPABASE (ANON KEY)
# =========================
SUPABASE_URL = st.secrets["SUPABASE_URL"]
SUPABASE_KEY = st.secrets["SUPABASE_ANON_KEY"]

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

ANNEE = 2025

# =========================
# HELPERS
# =========================
@st.cache_data(ttl=60)
def load_repartition(annee: int):
    return (
        supabase
        .table("repartition_par_lot")
        .select("*")
        .eq("annee", annee)
        .order("groupe_compte")
        .order("lot")
        .execute()
        .data
    )

@st.cache_data(ttl=60)
def load_controle(annee: int):
    return (
        supabase
        .table("repartition_par_lot_controle")
        .select("*")
        .eq("annee", annee)
        .order("groupe_compte")
        .execute()
        .data
    )

# =========================
# UI
# =========================
st.title("🏢 Pilotage des charges de l’immeuble")

tab1, tab2 = st.tabs([
    "📊 Répartition par lot",
    "✅ Contrôles budgétaires"
])

# =========================
# TAB 1 — RÉPARTITION
# =========================
with tab1:
    data = load_repartition(ANNEE)
    df = pd.DataFrame(data)

    if df.empty:
        st.warning("Aucune donnée de répartition.")
    else:
        st.dataframe(
            df,
            use_container_width=True,
            hide_index=True
        )

        st.download_button(
            "⬇️ Export CSV",
            df.to_csv(index=False).encode("utf-8"),
            file_name=f"repartition_lots_{ANNEE}.csv",
            mime="text/csv"
        )

# =========================
# TAB 2 — CONTROLES
# =========================
with tab2:
    data = load_controle(ANNEE)
    df = pd.DataFrame(data)

    if df.empty:
        st.warning("Aucun contrôle disponible.")
    else:
        st.dataframe(
            df,
            use_container_width=True,
            hide_index=True
        )

        erreurs = df[df["statut"] != "OK"]
        if not erreurs.empty:
            st.error("⚠️ Des incohérences ont été détectées.")
        else:
            st.success("✅ Tous les groupes sont cohérents.")

        st.download_button(
            "⬇️ Export contrôles CSV",
            df.to_csv(index=False).encode("utf-8"),
            file_name=f"controle_repartition_{ANNEE}.csv",
            mime="text/csv"
        )