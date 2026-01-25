import streamlit as st
import pandas as pd
from supabase import create_client

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
    return create_client(
        st.secrets["SUPABASE_URL"],
        st.secrets["SUPABASE_ANON_KEY"]
    )

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
    # MERGE
    # =========================
    df = df_rep.merge(
        df_dep,
        left_on="depense_id",
        right_on="id",
        how="left"
    )

    df["charges_reelles"] = df["montant_ttc"] * df["quote_part"] / BASE_TANTIEMES

    # =========================
    # FILTRES
    # =========================
    lot_choices = ["Tous"] + sorted(df["lot"].astype(str).unique())
    compte_choices = ["Tous"] + sorted(df["compte"].astype(str).unique())

    lot_filtre = st.sidebar.selectbox("Lot", lot_choices)
    compte_filtre = st.sidebar.selectbox("Compte", compte_choices)

    if lot_filtre != "Tous":
        df = df[df["lot"].astype(str) == lot_filtre]

    if compte_filtre != "Tous":
        df = df[df["compte"].astype(str) == compte_filtre]

    # =========================
    # CHARGES PAR LOT
    # =========================
    charges = df.groupby("lot", as_index=False)["charges_reelles"].sum()

    # =========================
    # BUDGET (ROBUSTE)
    # =========================
    try:
        budget_resp = (
            supabase
            .table("budgets")  # 👈 NOM CORRECT
            .select("montant")
            .eq("annee", annee)
            .execute()
        )

        total_budget = sum(b["montant"] for b in budget_resp.data)

    except Exception as e:
        st.error("❌ Erreur chargement budget")
        st.code(str(e))
        total_budget = 0

    df_lots["appel_fonds"] = total_budget * df_lots["tantiemes"] / BASE_TANTIEMES

    final = charges.merge(
        df_lots[["lot", "appel_fonds"]],
        on="lot",
        how="left"
    ).fillna(0)

    final["ecart"] = final["charges_reelles"] - final["appel_fonds"]

    # =========================
    # KPI
    # =========================
    c1, c2, c3 = st.columns(3)

    c1.metric("Charges réelles", euro(final["charges_reelles"].sum()))
    c2.metric("Appels de fonds", euro(final["appel_fonds"].sum()))
    c3.metric("Régularisation", euro(final["ecart"].sum()))

    # =========================
    # TABLE
    # =========================
    st.markdown("### 📋 Régularisation par lot")

    display = final.copy()
    display["Charges réelles (€)"] = display["charges_reelles"].apply(euro)
    display["Appels de fonds (€)"] = display["appel_fonds"].apply(euro)
    display["Écart (€)"] = display["ecart"].apply(euro)

    st.dataframe(
        display[["lot", "Charges réelles (€)", "Appels de fonds (€)", "Écart (€)"]],
        use_container_width=True
    )

if __name__ == "__main__":
    main()