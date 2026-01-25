import streamlit as st
import pandas as pd
from supabase import create_client

# =========================
# CONSTANTES
# =========================
BASE_TANTIEMES = 10_000

# =========================
# FORMAT €
# =========================
def eur(val):
    return f"{val:,.2f} €".replace(",", " ").replace(".", ",")

# =========================
# SUPABASE
# =========================
@st.cache_resource
def get_supabase():
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_ANON_KEY"]
    return create_client(url, key)

# =========================
# MAIN
# =========================
def main(supabase):
    st.set_page_config(page_title="Pilotage des charges", layout="wide")

    # =========================
    # SIDEBAR
    # =========================
    st.sidebar.title("Filtres")

    annee = st.sidebar.selectbox("Année", [2023, 2024, 2025, 2026], index=2)

    # =========================
    # LOTS
    # =========================
    lots_resp = supabase.table("lots").select("lot, tantiemes").execute()
    df_lots = pd.DataFrame(lots_resp.data)

    if df_lots.empty:
        st.error("Aucun lot trouvé.")
        return

    lots_list = ["Tous"] + sorted(df_lots["lot"].astype(str).tolist())
    lot_filtre = st.sidebar.selectbox("Lot", lots_list)

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
        st.warning("Aucune dépense pour cette année.")
        return

    comptes_list = ["Tous"] + sorted(df_dep["compte"].astype(str).unique().tolist())
    compte_filtre = st.sidebar.selectbox("Compte", comptes_list)

    if compte_filtre != "Tous":
        df_dep = df_dep[df_dep["compte"].astype(str) == compte_filtre]

    # =========================
    # RÉPARTITION
    # =========================
    rep_resp = supabase.table("repartition_depenses").select(
        "depense_id, lot_id, quote_part"
    ).execute()
    df_rep = pd.DataFrame(rep_resp.data)

    if df_rep.empty:
        st.warning("Aucune répartition trouvée.")
        return

    df_rep["quote_part"] = df_rep["quote_part"] / BASE_TANTIEMES

    # jointure
    df = (
        df_rep
        .merge(df_dep, left_on="depense_id", right_on="id")
        .merge(df_lots, left_on="lot_id", right_index=True)
    )

    df["charge_reelle"] = df["montant_ttc"] * df["quote_part"]

    # =========================
    # CHARGES PAR LOT
    # =========================
    charges = (
        df.groupby("lot", as_index=False)
        .agg(charges_reelles=("charge_reelle", "sum"))
    )

    if lot_filtre != "Tous":
        charges = charges[charges["lot"].astype(str) == lot_filtre]

    total_charges = charges["charges_reelles"].sum()

    # =========================
    # BUDGET / APPELS DE FONDS
    # =========================
    budget_resp = (
        supabase
        .table("budgets")
        .select("annee, budget")
        .eq("annee", annee)
        .execute()
    )

    total_budget = sum(b["budget"] for b in budget_resp.data) if budget_resp.data else 0

    df_lots["appel_fonds"] = total_budget * df_lots["tantiemes"] / BASE_TANTIEMES

    if lot_filtre != "Tous":
        df_lots = df_lots[df_lots["lot"].astype(str) == lot_filtre]

    # =========================
    # FINAL
    # =========================
    final = charges.merge(
        df_lots[["lot", "appel_fonds"]],
        on="lot",
        how="left"
    )

    final["appel_fonds"] = final["appel_fonds"].fillna(0)
    final["ecart"] = final["charges_reelles"] - final["appel_fonds"]

    # =========================
    # AFFICHAGE
    # =========================
    st.title("🏢 Pilotage des charges de l’immeuble")
    st.subheader("Charges par lot — Réel vs Appels de fonds")

    col1, col2, col3 = st.columns(3)
    col1.metric("Charges réelles totales", eur(total_charges))
    col2.metric("Appels de fonds totaux", eur(final["appel_fonds"].sum()))
    col3.metric("Régularisation globale", eur(final["ecart"].sum()))

    st.markdown("### 📋 Régularisation par lot")
    st.caption("Répartition basée sur 10 000 tantièmes")

    st.dataframe(
        final.rename(columns={
            "lot": "Lot",
            "charges_reelles": "Charges réelles (€)",
            "appel_fonds": "Appels de fonds (€)",
            "ecart": "Écart (€)"
        }).assign(
            **{
                "Charges réelles (€)": final["charges_reelles"].apply(eur),
                "Appels de fonds (€)": final["appel_fonds"].apply(eur),
                "Écart (€)": final["ecart"].apply(eur),
            }
        ),
        use_container_width=True
    )

# =========================
# RUN
# =========================
if __name__ == "__main__":
    supabase = get_supabase()
    main(supabase)