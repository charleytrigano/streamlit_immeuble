import streamlit as st
import pandas as pd
import os
from supabase import create_client

# =========================
# PARAMÈTRES MÉTIER
# =========================
BASE_TANTIEMES = 10_000
TOLERANCE = 0.01

# =========================
# APP
# =========================
def main(supabase):
    st.title("🏢 Pilotage des charges de l’immeuble")
    st.subheader("📊 Charges par lot – Réel vs Appels de fonds")

    # -------------------------
    # FILTRES
    # -------------------------
    col1, col2, col3 = st.columns(3)

    with col1:
        annee = st.selectbox("Année", [2023, 2024, 2025, 2026], index=2)

    # -------------------------
    # LOTS
    # -------------------------
    lots_resp = (
        supabase
        .table("lots")
        .select("id, lot, tantiemes")
        .execute()
    )

    if not lots_resp.data:
        st.error("Aucun lot trouvé.")
        return

    df_lots = pd.DataFrame(lots_resp.data)
    liste_lots = df_lots["lot"].astype(str).tolist()

    with col2:
        lot_filter = st.selectbox("Lot", ["Tous"] + liste_lots)

    # -------------------------
    # DÉPENSES
    # -------------------------
    dep_resp = (
        supabase
        .table("depenses")
        .select("id, annee, compte, montant_ttc")
        .eq("annee", annee)
        .execute()
    )

    if not dep_resp.data:
        st.warning("Aucune dépense pour cette année.")
        return

    df_dep = pd.DataFrame(dep_resp.data)
    liste_comptes = sorted(df_dep["compte"].astype(str).unique().tolist())

    with col3:
        compte_filter = st.selectbox("Compte", ["Tous"] + liste_comptes)

    # -------------------------
    # RÉPARTITIONS
    # -------------------------
    rep_resp = (
        supabase
        .table("repartition_depenses")
        .select("depense_id, lot_id, quote_part")
        .execute()
    )

    if not rep_resp.data:
        st.warning("Aucune répartition enregistrée.")
        return

    df_rep = pd.DataFrame(rep_resp.data)

    # -------------------------
    # JOINS
    # -------------------------
    df = (
        df_rep
        .merge(df_dep, left_on="depense_id", right_on="id", how="left")
        .merge(df_lots, left_on="lot_id", right_on="id", how="left", suffixes=("", "_lot"))
    )

    # -------------------------
    # FILTRES
    # -------------------------
    if lot_filter != "Tous":
        df = df[df["lot"].astype(str) == lot_filter]

    if compte_filter != "Tous":
        df = df[df["compte"].astype(str) == compte_filter]

    # -------------------------
    # CALCUL CHARGES RÉELLES
    # -------------------------
    df["charges_reelles"] = df["montant_ttc"] * df["quote_part"] / BASE_TANTIEMES

    charges_reelles = (
        df
        .groupby(["lot", "compte"], as_index=False)
        .agg(charges_reelles=("charges_reelles", "sum"))
    )

    # -------------------------
    # BUDGET / APPELS DE FONDS
    # -------------------------
    budget_resp = (
        supabase
        .table("budget")
        .select("annee, budget")
        .eq("annee", annee)
        .execute()
    )

    total_budget = sum(b["budget"] for b in budget_resp.data) if budget_resp.data else 0

    df_lots["appel_fonds"] = total_budget * df_lots["tantiemes"] / BASE_TANTIEMES

    final = charges_reelles.merge(
        df_lots[["lot", "appel_fonds"]],
        on="lot",
        how="left"
    )

    final["ecart"] = final["charges_reelles"] - final["appel_fonds"]

    # -------------------------
    # KPI
    # -------------------------
    col1, col2, col3 = st.columns(3)

    col1.metric("Total charges réelles (€)", f"{final['charges_reelles'].sum():,.2f}")
    col2.metric("Total appels de fonds (€)", f"{final['appel_fonds'].sum():,.2f}")
    col3.metric("Écart global (€)", f"{final['ecart'].sum():,.2f}")

    st.caption("ℹ️ Répartition basée sur 1 / 10 000 tantièmes")

    # -------------------------
    # TABLEAU FINAL
    # -------------------------
    st.markdown("### 📋 Régularisation des charges par lot")

    st.dataframe(
        final.rename(columns={
            "lot": "Lot",
            "compte": "Compte",
            "charges_reelles": "Charges réelles (€)",
            "appel_fonds": "Appels de fonds (€)",
            "ecart": "Écart à régulariser (€)"
        }).sort_values(["Lot", "Compte"]),
        use_container_width=True
    )


# =========================
# LANCEMENT
# =========================
if __name__ == "__main__":
    SUPABASE_URL = os.environ.get("SUPABASE_URL")
    SUPABASE_KEY = os.environ.get("SUPABASE_KEY")

    supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
    main(supabase)