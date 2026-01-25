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
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_ANON_KEY"]
    return create_client(url, key)

# =========================
# FORMAT €
# =========================
def eur(x: float) -> str:
    return f"{x:,.2f} €".replace(",", " ").replace(".", ",")

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

    # -------------------------
    # LOTS
    # -------------------------
    lots_resp = supabase.table("lots").select("id, lot, tantiemes").execute()
    df_lots = pd.DataFrame(lots_resp.data)

    if df_lots.empty:
        st.error("Aucun lot trouvé.")
        return

    df_lots["lot"] = df_lots["lot"].astype(str)
    df_lots["tantiemes"] = pd.to_numeric(df_lots["tantiemes"], errors="coerce").fillna(0)

    lot_filtre = st.sidebar.selectbox(
        "Lot",
        ["Tous"] + sorted(df_lots["lot"].unique())
    )

    # -------------------------
    # DÉPENSES (de l'année)
    # -------------------------
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

    df_dep["compte"] = df_dep["compte"].astype(str)
    df_dep["montant_ttc"] = pd.to_numeric(df_dep["montant_ttc"], errors="coerce").fillna(0)

    # Filtre compte (optionnel)
    compte_filtre = st.sidebar.selectbox(
        "Compte",
        ["Tous"] + sorted(df_dep["compte"].dropna().unique())
    )

    if compte_filtre != "Tous":
        df_dep = df_dep[df_dep["compte"] == compte_filtre]

    if df_dep.empty:
        st.warning("Aucune dépense après filtrage par compte.")
        return

    # On peut décider de ne prendre que les montants positifs (charges)
    # Ici je prends tout, avoirs compris, pour respecter la compta :
    total_charges = df_dep["montant_ttc"].sum()

    # -------------------------
    # BUDGETS (APPELS DE FONDS)
    # -------------------------
    bud_resp = (
        supabase
        .table("budgets")
        .select("annee, compte, budget")
        .eq("annee", annee)
        .execute()
    )
    df_bud = pd.DataFrame(bud_resp.data) if bud_resp.data else pd.DataFrame(columns=["budget"])

    df_bud["budget"] = pd.to_numeric(df_bud.get("budget", 0), errors="coerce").fillna(0)

    # Si tu veux ne prendre qu’un compte (ex : 71300100), décommente :
    # df_bud = df_bud[df_bud["compte"] == "71300100"]

    total_budget = df_bud["budget"].sum()

    # -------------------------
    # RÉPARTITION PAR LOT (PRORATA TANTIÈMES)
    # -------------------------
    df_lots_calc = df_lots.copy()

    # part de tantièmes du lot
    df_lots_calc["part_tantiemes"] = df_lots_calc["tantiemes"] / BASE_TANTIEMES

    # Charges réelles réparties par lot
    df_lots_calc["charges_reelles"] = total_charges * df_lots_calc["part_tantiemes"]

    # Appels de fonds répartis par lot
    df_lots_calc["appel_fonds"] = total_budget * df_lots_calc["part_tantiemes"]

    # Écart
    df_lots_calc["ecart"] = df_lots_calc["charges_reelles"] - df_lots_calc["appel_fonds"]

    # Filtre lot (après calcul pour garder cohérence des totaux)
    if lot_filtre != "Tous":
        df_lots_aff = df_lots_calc[df_lots_calc["lot"] == lot_filtre].copy()
    else:
        df_lots_aff = df_lots_calc.copy()

    # =========================
    # UI
    # =========================
    st.title("🏢 Pilotage des charges de l’immeuble")
    st.subheader("Charges par lot — Réel vs Appels de fonds")

    col1, col2, col3 = st.columns(3)

    col1.metric(
        "Charges réelles totales (dépenses)",
        eur(total_charges)
    )
    col2.metric(
        "Appels de fonds totaux (budgets)",
        eur(total_budget)
    )
    col3.metric(
        "Régularisation globale",
        eur(df_lots_calc["ecart"].sum())
    )

    st.markdown("### 📋 Détail par lot")
    st.caption("Répartition basée sur 10 000 tantièmes (prorata simples)")

    df_aff = df_lots_aff[["lot", "appel_fonds", "charges_reelles", "ecart"]].copy()
    df_aff.rename(columns={
        "lot": "Lot",
        "appel_fonds": "Appels de fonds (€)",
        "charges_reelles": "Charges réelles (€)",
        "ecart": "Écart (€)"
    }, inplace=True)

    # Formatage € pour le tableau
    for col in ["Appels de fonds (€)", "Charges réelles (€)", "Écart (€)"]:
        df_aff[col] = df_aff[col].apply(eur)

    st.dataframe(df_aff, use_container_width=True)

# =========================
# RUN
# =========================
if __name__ == "__main__":
    main()