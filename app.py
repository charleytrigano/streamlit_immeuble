import streamlit as st
import pandas as pd
from supabase import create_client

# =========================
# CONFIG
# =========================
BASE_TANTIEMES = 10_000

def euro(x):
    return f"{x:,.2f} €".replace(",", " ").replace(".", ",")

# =========================
# CONNEXION SUPABASE
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

    # =========================
    # SIDEBAR
    # =========================
    st.sidebar.title("⚙️ Paramètres")

    annee = st.sidebar.selectbox(
        "Année",
        [2023, 2024, 2025, 2026],
        index=2
    )

    # =========================
    # TITRE
    # =========================
    st.title("🏢 Pilotage des charges de l’immeuble")
    st.subheader("Charges par lot — Réel vs Appels de fonds")

    # =========================
    # LOTS
    # =========================
    lots_resp = (
        supabase
        .table("lots")
        .select("lot, tantiemes")
        .execute()
    )

    if not lots_resp.data:
        st.error("Aucun lot trouvé.")
        return

    df_lots = pd.DataFrame(lots_resp.data)

    lot_filtre = st.sidebar.selectbox(
        "Lot",
        ["Tous"] + sorted(df_lots["lot"].astype(str).tolist())
    )

    # =========================
    # DEPENSES + REPARTITION
    # =========================
    dep_resp = (
        supabase
        .table("depenses")
        .select("id, annee, montant_ttc")
        .eq("annee", annee)
        .execute()
    )

    if not dep_resp.data:
        st.warning("Aucune dépense pour cette année.")
        return

    df_dep = pd.DataFrame(dep_resp.data)

    rep_resp = (
        supabase
        .table("repartition_depenses")
        .select("depense_id, lot_id, quote_part")
        .execute()
    )

    if not rep_resp.data:
        st.warning("Aucune répartition trouvée.")
        return

    df_rep = pd.DataFrame(rep_resp.data)

    # jointure lots
    df_rep = df_rep.merge(
        df_lots.reset_index().rename(columns={"index": "lot_id"}),
        on="lot_id",
        how="left"
    )

    # jointure dépenses
    df = df_rep.merge(
        df_dep,
        left_on="depense_id",
        right_on="id",
        how="left"
    )

    # calcul charges réelles
    df["charges_reelles"] = df["montant_ttc"] * df["quote_part"]

    if lot_filtre != "Tous":
        df = df[df["lot"].astype(str) == lot_filtre]

    charges_reelles = (
        df.groupby("lot", as_index=False)
        .agg(charges_reelles=("charges_reelles", "sum"))
    )

    # =========================
    # BUDGET / APPELS DE FONDS
    # =========================
    budget_resp = (
        supabase
        .table("budget")
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
    final = charges_reelles.merge(
        df_lots[["lot", "appel_fonds"]],
        on="lot",
        how="left"
    ).fillna(0)

    final["ecart"] = final["charges_reelles"] - final["appel_fonds"]

    # =========================
    # KPI
    # =========================
    c1, c2, c3 = st.columns(3)

    c1.metric(
        "Charges réelles totales",
        euro(final["charges_reelles"].sum())
    )

    c2.metric(
        "Appels de fonds totaux",
        euro(final["appel_fonds"].sum())
    )

    c3.metric(
        "Régularisation globale",
        euro(final["ecart"].sum())
    )

    # =========================
    # TABLEAU
    # =========================
    st.markdown("### 📋 Régularisation par lot")

    st.caption("Répartition basée sur 10 000 tantièmes")

    st.dataframe(
        final.assign(
            **{
                "Charges réelles (€)": final["charges_reelles"].map(euro),
                "Appels de fonds (€)": final["appel_fonds"].map(euro),
                "Régularisation (€)": final["ecart"].map(euro),
            }
        )[[
            "lot",
            "Charges réelles (€)",
            "Appels de fonds (€)",
            "Régularisation (€)"
        ]],
        use_container_width=True
    )

    st.info(
        "Régularisation > 0 : le copropriétaire doit payer\n\n"
        "Régularisation < 0 : le copropriétaire doit être remboursé"
    )

# =========================
# LANCEMENT
# =========================
if __name__ == "__main__":
    supabase = get_supabase()
    main(supabase)
