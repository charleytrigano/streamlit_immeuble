import streamlit as st
import pandas as pd
from supabase import create_client

# =========================
# CONFIG
# =========================
st.set_page_config(
    page_title="Pilotage des charges de l’immeuble",
    layout="wide"
)

# =========================
# SUPABASE
# =========================
@st.cache_resource
def get_supabase():
    return create_client(
        st.secrets["SUPABASE_URL"],
        st.secrets["SUPABASE_ANON_KEY"]
    )

# =========================
# MAIN
# =========================
def main():
    supabase = get_supabase()

    # =========================
    # FILTRES
    # =========================
    st.sidebar.title("Filtres")

    annee = st.sidebar.selectbox("Année", [2023, 2024, 2025, 2026], index=2)

    # =========================
    # LOTS
    # =========================
    df_lots = pd.DataFrame(
        supabase.table("lots")
        .select("id, lot, tantiemes")
        .execute()
        .data
    )

    if df_lots.empty:
        st.error("Aucun lot trouvé")
        return

    df_lots["lot"] = df_lots["lot"].astype(str)

    lot_filtre = st.sidebar.selectbox(
        "Lot",
        ["Tous"] + sorted(df_lots["lot"].unique())
    )

    # =========================
    # DÉPENSES
    # =========================
    df_dep = pd.DataFrame(
        supabase.table("depenses")
        .select("id, montant_ttc, compte, annee")
        .eq("annee", annee)
        .execute()
        .data
    )

    if df_dep.empty:
        st.warning("Aucune dépense pour cette année")
        return

    df_dep["compte"] = df_dep["compte"].fillna("Non renseigné")

    compte_filtre = st.sidebar.selectbox(
        "Compte",
        ["Tous"] + sorted(df_dep["compte"].unique())
    )

    # =========================
    # RÉPARTITION
    # =========================
    df_rep = pd.DataFrame(
        supabase.table("repartition_depenses")
        .select("depense_id, lot_id, quote_part")
        .execute()
        .data
    )

    if df_rep.empty:
        st.error("Aucune répartition trouvée")
        return

    # =========================
    # CONTRÔLE DE COHÉRENCE (OBLIGATOIRE)
    # =========================
    controle = (
        df_rep.groupby("depense_id", as_index=False)
        .agg(total_quote=("quote_part", "sum"))
    )

    anomalies = controle[~controle["total_quote"].between(0.999, 1.001)]

    if not anomalies.empty:
        st.error("❌ Certaines dépenses ne sont PAS réparties à 100 %")
        st.dataframe(anomalies)
        return

    # =========================
    # MERGE GLOBAL
    # =========================
    df = (
        df_rep
        .merge(df_dep, left_on="depense_id", right_on="id", how="left")
        .merge(df_lots, left_on="lot_id", right_on="id", how="left", suffixes=("", "_lot"))
    )

    if compte_filtre != "Tous":
        df = df[df["compte"] == compte_filtre]

    if lot_filtre != "Tous":
        df = df[df["lot"] == lot_filtre]

    # =========================
    # CALCUL DES CHARGES RÉELLES (CORRECT)
    # =========================
    df["charge_reelle"] = df["montant_ttc"] * df["quote_part"]

    charges_lot = (
        df.groupby("lot", as_index=False)
        .agg(charges_reelles=("charge_reelle", "sum"))
    )

    # =========================
    # BUDGET
    # =========================
    df_budget = pd.DataFrame(
        supabase.table("budgets")
        .select("montant")
        .eq("annee", annee)
        .execute()
        .data
    )

    budget_total = df_budget["montant"].sum() if not df_budget.empty else 0

    df_lots["appel_fonds"] = (
        budget_total * df_lots["tantiemes"] / df_lots["tantiemes"].sum()
    )

    if lot_filtre != "Tous":
        df_lots = df_lots[df_lots["lot"] == lot_filtre]

    # =========================
    # TABLEAU FINAL
    # =========================
    final = (
        df_lots[["lot", "appel_fonds"]]
        .merge(charges_lot, on="lot", how="left")
        .fillna(0)
    )

    final["ecart"] = final["charges_reelles"] - final["appel_fonds"]

    # =========================
    # UI
    # =========================
    st.title("🏢 Pilotage des charges de l’immeuble")
    st.subheader("Charges par lot — Réel vs Budget")

    col1, col2, col3 = st.columns(3)

    col1.metric("Charges réelles totales", f"{final['charges_reelles'].sum():,.2f} €")
    col2.metric("Appels de fonds totaux", f"{final['appel_fonds'].sum():,.2f} €")
    col3.metric("Régularisation globale", f"{final['ecart'].sum():,.2f} €")

    st.markdown("### 📋 Régularisation par lot")
    st.dataframe(final, use_container_width=True)

    # =========================
    # DÉTAIL PAR COMPTE
    # =========================
    st.markdown("### 📊 Détail des dépenses par compte")

    dep_compte = (
        df.groupby("compte", as_index=False)
        .agg(
            montant_facture=("montant_ttc", "sum"),
            charges_reparties=("charge_reelle", "sum")
        )
        .sort_values("charges_reparties", ascending=False)
    )

    st.dataframe(dep_compte, use_container_width=True)

# =========================
# RUN
# =========================
if __name__ == "__main__":
    main()