import streamlit as st
import pandas as pd
from supabase import create_client

# =========================
# CONFIG
# =========================
BASE_TANTIEMES = 10_000

st.set_page_config(
    page_title="Pilotage des charges",
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

def euro(val):
    return f"{val:,.2f} €".replace(",", " ").replace(".", ",")

# =========================
# MAIN
# =========================
def main():
    supabase = get_supabase()

    # =========================
    # SIDEBAR – FILTRES
    # =========================
    st.sidebar.title("Filtres")

    annee = st.sidebar.selectbox(
        "Année",
        [2023, 2024, 2025, 2026],
        index=2
    )

    # =========================
    # LOTS
    # =========================
    lots_resp = (
        supabase
        .table("lots")
        .select("id, lot, tantiemes")
        .execute()
    )
    df_lots = pd.DataFrame(lots_resp.data)

    if df_lots.empty:
        st.error("Aucun lot trouvé")
        return

    df_lots["lot"] = df_lots["lot"].astype(str)
    df_lots["tantiemes"] = pd.to_numeric(df_lots["tantiemes"], errors="coerce").fillna(0)

    lot_filtre = st.sidebar.selectbox(
        "Lot",
        ["Tous"] + sorted(df_lots["lot"].unique().tolist())
    )

    # =========================
    # DÉPENSES
    # =========================
    dep_resp = (
        supabase
        .table("depenses")
        .select("id, montant_ttc, compte, annee")
        .eq("annee", annee)
        .execute()
    )
    df_dep = pd.DataFrame(dep_resp.data)

    if df_dep.empty:
        st.warning("Aucune dépense pour cette année")
        return

    df_dep["montant_ttc"] = pd.to_numeric(df_dep["montant_ttc"], errors="coerce").fillna(0)
    df_dep["compte"] = df_dep["compte"].astype(str).fillna("Non renseigné")

    compte_filtre = st.sidebar.selectbox(
        "Compte",
        ["Tous"] + sorted(df_dep["compte"].unique().tolist())
    )

    # =========================
    # RÉPARTITION DES DÉPENSES
    # =========================
    rep_resp = (
        supabase
        .table("repartition_depenses")
        .select("depense_id, lot_id, quote_part")
        .execute()
    )
    df_rep = pd.DataFrame(rep_resp.data)

    if df_rep.empty:
        st.error("Aucune répartition trouvée")
        return

    df_rep["quote_part"] = pd.to_numeric(df_rep["quote_part"], errors="coerce").fillna(0)

    # =========================
    # MERGE GLOBAL
    # =========================
    df = (
        df_rep
        .merge(df_dep, left_on="depense_id", right_on="id", how="left")
        .merge(
            df_lots,
            left_on="lot_id",
            right_on="id",
            how="left",
            suffixes=("", "_lot")
        )
    )

    if compte_filtre != "Tous":
        df = df[df["compte"] == compte_filtre]

    if lot_filtre != "Tous":
        df = df[df["lot"] == lot_filtre]

    # =========================
    # CHARGES RÉELLES (TANTIÈMES)
    # =========================
    df["charges_reelles"] = (
        df["montant_ttc"] * df["quote_part"] / BASE_TANTIEMES
    )

    charges_lot = (
        df
        .groupby("lot", as_index=False)
        .agg(charges_reelles=("charges_reelles", "sum"))
    )

    # =========================
    # BUDGET / APPELS DE FONDS
    # =========================
    budget_resp = (
        supabase
        .table("budgets")
        .select("montant")
        .eq("annee", annee)
        .execute()
    )

    budget_total = sum(
        pd.to_numeric(b["montant"], errors="coerce")
        for b in budget_resp.data
    ) if budget_resp.data else 0

    df_lots_calc = df_lots.copy()
    df_lots_calc["appel_fonds"] = (
        budget_total * df_lots_calc["tantiemes"] / BASE_TANTIEMES
    )

    if lot_filtre != "Tous":
        df_lots_calc = df_lots_calc[df_lots_calc["lot"] == lot_filtre]

    # =========================
    # FINAL PAR LOT
    # =========================
    final = (
        df_lots_calc[["lot", "appel_fonds"]]
        .merge(charges_lot, on="lot", how="left")
        .fillna(0)
    )

    final["ecart"] = final["charges_reelles"] - final["appel_fonds"]

    # =========================
    # UI – KPI
    # =========================
    st.title("🏢 Pilotage des charges de l’immeuble")
    st.subheader("Charges par lot — Réel vs Appels de fonds")

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
    # TABLEAU PAR LOT
    # =========================
    st.markdown("### 📋 Régularisation par lot")

    st.dataframe(
        final.rename(columns={
            "lot": "Lot",
            "charges_reelles": "Charges réelles (€)",
            "appel_fonds": "Appels de fonds (€)",
            "ecart": "Écart (€)"
        }),
        use_container_width=True
    )

    # =========================
    # DÉTAIL PAR COMPTE
    # =========================
    st.markdown("### 📊 Détail des dépenses par compte")

    dep_compte = (
        df
        .groupby("compte", as_index=False)
        .agg(
            montant_total=("montant_ttc", "sum"),
            charges_reelles=("charges_reelles", "sum")
        )
        .sort_values("charges_reelles", ascending=False)
    )

    dep_compte["montant_total"] = dep_compte["montant_total"].apply(euro)
    dep_compte["charges_reelles"] = dep_compte["charges_reelles"].apply(euro)

    st.dataframe(
        dep_compte.rename(columns={
            "compte": "Compte",
            "montant_total": "Montant facturé (€)",
            "charges_reelles": "Charges réparties (€)"
        }),
        use_container_width=True
    )

# =========================
# RUN
# =========================
if __name__ == "__main__":
    main()