import streamlit as st
import pandas as pd
from supabase import create_client, Client

# --------------------------------------------------
# CONFIG STREAMLIT
# --------------------------------------------------
st.set_page_config(
    page_title="Pilotage des charges",
    layout="wide"
)

st.title("📊 Pilotage des charges de l’immeuble")

# --------------------------------------------------
# SUPABASE CONNECTION (ANON KEY)
# --------------------------------------------------
SUPABASE_URL = st.secrets["SUPABASE_URL"]
SUPABASE_ANON_KEY = st.secrets["SUPABASE_ANON_KEY"]

supabase: Client = create_client(
    SUPABASE_URL,
    SUPABASE_ANON_KEY
)

# --------------------------------------------------
# PARAMÈTRES
# --------------------------------------------------
annee = st.selectbox(
    "Année",
    options=[2023, 2024, 2025],
    index=2
)

# --------------------------------------------------
# ONGLET
# --------------------------------------------------
tab1, tab2 = st.tabs([
    "📋 Répartition par lot",
    "✅ Contrôle répartition"
])

# ==================================================
# ONGLET 1 — RÉPARTITION PAR LOT
# ==================================================
with tab1:
    st.subheader("Répartition des charges par lot")

    try:
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
            st.info("Aucune donnée disponible")
        else:
            df = pd.DataFrame(res.data)

            # Mise en forme
            df = df.rename(columns={
                "lot": "Lot",
                "groupe_compte": "Groupe",
                "libelle_groupe": "Libellé",
                "tantiemes": "Tantièmes",
                "part_lot": "Part (€)"
            })

            st.dataframe(
                df,
                use_container_width=True
            )

    except Exception as e:
        st.error("Erreur lors du chargement de la répartition")
        st.exception(e)

# ==================================================
# ONGLET 2 — CONTRÔLE
# ==================================================
with tab2:
    st.subheader("Contrôle des répartitions")

    try:
        res_ctrl = (
            supabase
            .table("repartition_par_lot_controle")
            .select("*")
            .eq("annee", annee)
            .order("groupe_compte")
            .execute()
        )

        if not res_ctrl.data:
            st.info("Aucune donnée de contrôle")
        else:
            df_ctrl = pd.DataFrame(res_ctrl.data)

            df_ctrl = df_ctrl.rename(columns={
                "groupe_compte": "Groupe",
                "budget": "Budget (€)",
                "total_reparti": "Total réparti (€)",
                "ecart": "Écart (€)",
                "statut": "Statut"
            })

            st.dataframe(
                df_ctrl,
                use_container_width=True
            )

            # Alertes
            erreurs = df_ctrl[df_ctrl["Statut"] != "OK"]
            if not erreurs.empty:
                st.warning("⚠️ Des écarts ont été détectés")
            else:
                st.success("✅ Toutes les répartitions sont correctes")

    except Exception as e:
        st.error("Erreur lors du chargement du contrôle")
        st.exception(e)

# --------------------------------------------------
# FOOTER
# --------------------------------------------------
st.caption("Données issues de Supabase — accès ANON sécurisé par RLS")