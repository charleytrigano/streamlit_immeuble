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

# =========================
# MAIN
# =========================
def main():
    supabase = get_supabase()

    # =========================
    # FILTRES
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
    lots_resp = supabase.table("lots").select("id, lot, tantiemes").execute()
    df_lots = pd.DataFrame(lots_resp.data)

    if df_lots.empty:
        st.error("Aucun lot trouvé")
        return

    df_lots["lot"] = df_lots["lot"].astype(str)

    lot_filtre = st.sidebar.selectbox(
        "Lot",
        ["Tous"] + sorted(df_lots["lot"].unique().tolist())
    )

    # =========================
    # DÉPENSES (BRUT)
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

    df_dep["compte"] = df_dep["compte"].fillna("Non renseigné")

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

    # =========================
    # MERGE MÉTIER (CRITIQUE)
    # =========================
    df = (
        df_rep
        .merge(df_dep, left_on="depense_id", right_on="id", how="left")
        .merge(df_lots, left_on="lot_id", right_on="id", how="left", suffixes=("", "_lot"))
    )

    # =========================
    # CONTRÔLE RÉPARTITION
    # =========================
    controle = (
        df
        .groupby("depense_id", as_index=False)
        .agg(total_quote=("quote_part", "sum"))
    )

    if not (controle["total_quote"] == BASE_TANTIEMES).all():
        st.error("❌ Certaines dépenses ne sont PAS réparties à 100 %")
        st.dataframe(controle[controle["total_quote"] != BASE_TANTIEMES])
        return

    # =========================
    # FILTRES (APRÈS MERGE)
    # =========================
    if compte_filtre != "Tous":
        df = df[df["compte"] == compte_filtre]

    if lot_filtre != "Tous":
        df = df[df["lot"] == lot_filtre]

    # =========================
    # CHARGES RÉELLES (FORMULE JUSTE)
    # =========================
    df["charge_reelle"] = df["montant_ttc"] * df["quote_part"] / BASE_TANTIEMES

    charges_lot = (
        df
        .groupby("lot", as_index=False)
        .agg(charges_reelles=("charge_reelle", "sum"))
    )

    total_charges_reelles = charges_lot["charges_reelles"].sum()

    # =========================
    # BUDGET
    # =========================
    budget_resp = (
        supabase
        .table("budgets")
        .select("budget")
        .eq("annee", annee)
        .execute()
    )

    budget_total = sum(b["budget"] for b in budget_resp.data) if budget_resp.data else 0

    df_lots["appel_fonds"] = (
        budget_total * df_lots["tantiemes"] / BASE_TANTIEMES
    )

    if lot_filtre != "Tous":
        df_lots = df_lots[df_lots["lot"] == lot_filtre]

    total_appels = df_lots["appel_fonds"].sum()

    # =========================
    # TABLEAU FINAL PAR LOT
    # =========================
    final = (
        df_lots[["lot", "appel_fonds"]]
        .merge(charges_lot, on="lot", how="left")
        .fillna(0)
    )

    final["ecart"] = final["charges_reelles"] - final["appel_fonds"]

    # =========================
    # UI – KPI
    # =========================
    st.title("🏢 Pilotage des charges de l’immeuble")
    st.subheader("Charges par lot — Réel vs Appels de fonds")

    c1, c2, c3 = st.columns(3)

    c1.metric(
        "Charges réelles totales",
        f"{total_charges_reelles:,.2f} €".replace(",", " ").replace(".", ",")
    )
    c2.metric(
        "Appels de fonds totaux",
        f"{total_appels:,.2f} €".replace(",", " ").replace(".", ",")
    )
    c3.metric(
        "Régularisation globale",
        f"{(total_charges_reelles - total_appels):,.2f} €".replace(",", " ").replace(".", ",")
    )

    # =========================
    # TABLE PAR LOT
    # =========================
    st.markdown("### 📋 Régularisation par lot")

    st.dataframe(
        final.rename(columns={
            "lot": "Lot",
            "appel_fonds": "Appels de fonds (€)",
            "charges_reelles": "Charges réelles (€)",
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
            montant_facture=("montant_ttc", "sum"),
            charges_reparties=("charge_reelle", "sum")
        )
        .sort_values("charges_reparties", ascending=False)
    )

    st.dataframe(
        dep_compte.rename(columns={
            "compte": "Compte",
            "montant_facture": "Montant facturé (€)",
            "charges_reparties": "Charges réparties (€)"
        }),
        use_container_width=True
    )

    # =========================
    # CONTRÔLE FINAL
    # =========================
    st.markdown("### ✅ Contrôle de cohérence")

    st.write(
        f"Total dépenses réparties = **{df['charge_reelle'].sum():,.2f} €**  \n"
        f"Total dépenses brutes = **{df_dep['montant_ttc'].sum():,.2f} €**"
        .replace(",", " ").replace(".", ",")
    )

# =========================
# RUN
# =========================
if __name__ == "__main__":
    main()