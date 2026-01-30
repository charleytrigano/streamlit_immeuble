import streamlit as st
import pandas as pd
from supabase import create_client, Client

# =========================
# CONFIG
# =========================
st.set_page_config(
    page_title="Pilotage des charges",
    layout="wide"
)

SUPABASE_URL = st.secrets["SUPABASE_URL"]
SUPABASE_KEY = st.secrets["SUPABASE_SERVICE_ROLE_KEY"]

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# =========================
# SIDEBAR
# =========================
st.sidebar.title("Paramètres")

annee = st.sidebar.selectbox(
    "Année",
    [2024, 2025, 2026],
    index=1
)

# =========================
# TITRE
# =========================
st.title("🏢 Pilotage des charges de l’immeuble")

tabs = st.tabs([
    "📊 Répartition par lot",
    "🧮 Contrôle répartition"
])

# ======================================================
# ONGLET 1 — RÉPARTITION PAR LOT
# ======================================================
with tabs[0]:

    st.subheader("Répartition des charges par lot")

    res = (
        supabase
        .table("repartition_par_lot")
        .select("*")
        .eq("annee", annee)
        .order("groupe_compte")
        .order("lot")
        .execute()
    )

    if not res.data:
        st.warning("Aucune donnée pour cette année.")
    else:
        df = pd.DataFrame(res.data)

        df["part_lot"] = df["part_lot"].astype(float).round(2)

        st.dataframe(
            df,
            use_container_width=True,
            hide_index=True
        )

        st.markdown("### 🔢 Total réparti")
        st.metric(
            label="Total €",
            value=f"{df['part_lot'].sum():,.2f} €".replace(",", " ")
        )

# ======================================================
# ONGLET 2 — CONTRÔLE
# ======================================================
with tabs[1]:

    st.subheader("Contrôle budget vs répartition")

    res_ctrl = (
        supabase
        .table("repartition_par_lot_controle")
        .select("*")
        .eq("annee", annee)
        .order("groupe_compte")
        .execute()
    )

    if not res_ctrl.data:
        st.warning("Aucune donnée de contrôle.")
    else:
        df_ctrl = pd.DataFrame(res_ctrl.data)

        for col in ["budget_groupe", "total_reparti", "ecart"]:
            df_ctrl[col] = df_ctrl[col].astype(float).round(2)

        st.dataframe(
            df_ctrl,
            use_container_width=True,
            hide_index=True
        )

        st.markdown("### 🚨 Écarts détectés")

        df_alert = df_ctrl[df_ctrl["ecart"] != 0]

        if df_alert.empty:
            st.success("Aucun écart détecté 🎉")
        else:
            st.error("Des écarts existent entre budget et répartition")
            st.dataframe(
                df_alert,
                use_container_width=True,
                hide_index=True
            )

# =========================
# FOOTER
# =========================
st.caption("Pilotage des charges — Supabase × Streamlit")