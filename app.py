import streamlit as st
import pandas as pd
from supabase import create_client

# =========================
# CONFIG
# =========================
BASE_TANTIEMES = 10_000

st.set_page_config(
    page_title="Pilotage des charges de l’immeuble",
    layout="wide"
)

# =========================
# SUPABASE
# =========================
@st.cache_resource
def get_supabase():
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_ANON_KEY"]
    return create_client(url, key)

supabase = get_supabase()

# =========================
# FORMAT €
# =========================
def euro(x):
    return f"{x:,.2f} €".replace(",", " ").replace(".", ",")

# =========================
# APP
# =========================
def main():
    st.title("🏢 Pilotage des charges de l’immeuble")
    st.subheader("Charges par lot — Réel vs Appels de fonds")

    # =========================
    # SIDEBAR
    # =========================
    st.sidebar.header("Filtres")

    annee = st.sidebar.selectbox("Année", [2023, 2024, 2025, 2026], index=2)

    # =========================
    # DEPENSES
    # =========================
    dep_resp = (
        supabase
        .table("depenses")
        .select("id, montant_ttc, compte")
        .eq("annee", annee)
        .execute()
    )

    if not dep_resp.data:
        st.warning("Aucune dépense pour cette année.")
        return

    df_dep = pd.DataFrame(dep_resp.data)

    # =========================
    # REPARTITION
    # =========================
    rep_resp = (
        supabase
        .table("repartition_depenses")
        .select("depense_id, lot, quote_part")
        .execute()
    )

    df_rep = pd.DataFrame(rep_resp.data)

    # =========================
    # LOTS
    # =========================
    lots_resp = supabase.table("lots").select("lot, tantiemes").execute()
    df_lots = pd.DataFrame(lots_resp.data)

    # =========================
    # MERGE DEPENSES x REPARTITION
    # =========================
    df = df_rep.merge(
        df_dep,
        left_on="depense_id",
        right_on="id",
        how="left"
    )

    df["charges_reelles"] = (
        df["montant_ttc"] * df["quote_part"] / BASE_TANTIEMES
    )

    # =========================
    # FILTRES SIDEBAR
    # =========================
    lots = ["Tous"] + sorted(df["lot"].astype(str).unique().tolist())
    comptes = ["Tous"] + sorted(df["compte"].astype(str).unique().tolist())

    lot_filtre = st.sidebar.selectbox("Lot", lots)
    compte_filtre = st.sidebar.selectbox("Compte", comptes)

    if lot_filtre != "Tous":
        df = df[df["lot"].astype(str) == lot_filtre]

    if compte_filtre != "Tous":
        df = df[df["compte"].astype(str) == compte_filtre]

    # =========================
    # CHARGES REELLES PAR LOT
    # =========================
    charges_reelles = (
        df
        .groupby("lot", as_index=False)
        .agg(charges_reelles=("charges_reelles", "sum"))
    )

    # =========================
    # BUDGET / APPELS DE FONDS
    # =========================
    budget_resp = (
        supabase
        .table("budget")
        .select("montant")
        .eq("annee", annee)
        .execute()
    )

    total_budget = sum(b["montant"] for b in budget_resp.data)

    df_lots["appel_fonds"] = (
        total_budget * df_lots["tantiemes"] / BASE_TANTIEMES
    )

    final = charges_reelles.merge(
        df_lots[["lot", "appel_fonds"]],
        on="lot",
        how="left"
    ).fillna(0)

    final["ecart"] = final["charges_reelles"] - final["appel_fonds"]

    # =========================
    # KPI
    # =========================
    col1, col2, col3 = st.columns(3)

    col1.metric(
        "Charges réelles totales",
        euro(final["charges_reelles"].sum())
    )

    col2.metric(
        "Appels de fonds totaux",
        euro(final["appel_fonds"].sum())
    )

    col3.metric(
        "Régularisation globale",
        euro(final["ecart"].sum())
    )

    # =========================
    # TABLEAU
    # =========================
    st.markdown("### 📋 Régularisation par lot")
    st.caption("Répartition basée sur 10 000 tantièmes")

    final_display = final.copy()
    final_display["Charges réelles (€)"] = final_display["charges_reelles"].apply(euro)
    final_display["Appels de fonds (€)"] = final_display["appel_fonds"].apply(euro)
    final_display["Écart (€)"] = final_display["ecart"].apply(euro)

    st.dataframe(
        final_display[[
            "lot",
            "Charges réelles (€)",
            "Appels de fonds (€)",
            "Écart (€)"
        ]],
        use_container_width=True
    )

# =========================
# RUN
# =========================
if __name__ == "__main__":
    main()