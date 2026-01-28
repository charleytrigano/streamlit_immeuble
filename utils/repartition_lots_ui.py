import streamlit as st
import pandas as pd

# =========================
# CONSTANTES MÉTIER
# =========================
BASE_TANTIEMES = 10_000
TAUX_LOI_ALUR = 0.05  # 5 %

def euro(x):
    try:
        return f"{x:,.2f} €".replace(",", " ").replace(".", ",")
    except Exception:
        return "0,00 €"


def repartition_lots_ui(supabase, annee: int):
    st.header("🏢 Répartition des charges par lot")

    # =========================
    # CHARGEMENT DES DONNÉES
    # =========================
    dep_resp = (
        supabase
        .table("depenses")
        .select("depense_id, montant_ttc, annee")
        .eq("annee", annee)
        .execute()
    )
    df_dep = pd.DataFrame(dep_resp.data)

    rep_resp = (
        supabase
        .table("repartition_depenses")
        .select("depense_id, lot_id, quote_part")
        .execute()
    )
    df_rep = pd.DataFrame(rep_resp.data)

    lots_resp = (
        supabase
        .table("lots")
        .select("lot_id, lot, tantiemes")
        .execute()
    )
    df_lots = pd.DataFrame(lots_resp.data)

    bud_resp = (
        supabase
        .table("budgets")
        .select("budget")
        .eq("annee", annee)
        .execute()
    )
    df_bud = pd.DataFrame(bud_resp.data)

    # =========================
    # CONTRÔLES DE BASE
    # =========================
    if df_dep.empty or df_rep.empty or df_lots.empty:
        st.warning("Données insuffisantes pour calculer la répartition.")
        return

    # =========================
    # CHARGES RÉELLES PAR LOT
    # =========================
    df = (
        df_rep
        .merge(df_dep, on="depense_id", how="left")
        .merge(df_lots, on="lot_id", how="left")
    )

    df["charges_reelles"] = (
        df["montant_ttc"].fillna(0)
        * df["quote_part"].fillna(0)
        / BASE_TANTIEMES
    )

    charges_lot = (
        df
        .groupby(["lot_id", "lot"], as_index=False)
        .agg(charges_reelles=("charges_reelles", "sum"))
    )

    # =========================
    # APPELS DE FONDS
    # =========================
    budget_total = df_bud["budget"].sum() if not df_bud.empty else 0

    df_lots_calc = df_lots.copy()

    df_lots_calc["appel_budget"] = (
        budget_total
        * df_lots_calc["tantiemes"].fillna(0)
        / BASE_TANTIEMES
    )

    df_lots_calc["loi_alur"] = df_lots_calc["appel_budget"] * TAUX_LOI_ALUR
    df_lots_calc["appel_total"] = (
        df_lots_calc["appel_budget"] + df_lots_calc["loi_alur"]
    )

    # =========================
    # TABLEAU FINAL
    # =========================
    final = (
        df_lots_calc
        .merge(charges_lot, on=["lot_id", "lot"], how="left")
        .fillna(0)
    )

    final["ecart"] = final["charges_reelles"] - final["appel_total"]
    final["ecart_pct"] = final.apply(
        lambda r: (r["ecart"] / r["appel_total"] * 100)
        if r["appel_total"] != 0 else 0,
        axis=1
    )

    # =========================
    # KPI GLOBAUX
    # =========================
    col1, col2, col3, col4 = st.columns(4)

    col1.metric("💰 Budget total", euro(budget_total))
    col2.metric("📤 Appels de fonds", euro(final["appel_total"].sum()))
    col3.metric("⚖️ Charges réelles", euro(final["charges_reelles"].sum()))
    col4.metric("📉 Régularisation", euro(final["ecart"].sum()))

    # =========================
    # TABLEAU DÉTAILLÉ
    # =========================
    st.markdown("### 📋 Détail par lot")

    st.dataframe(
        final[[
            "lot",
            "appel_budget",
            "loi_alur",
            "appel_total",
            "charges_reelles",
            "ecart",
            "ecart_pct"
        ]]
        .rename(columns={
            "lot": "Lot",
            "appel_budget": "Appel budget (€)",
            "loi_alur": "Loi ALUR (5 %) (€)",
            "appel_total": "Total appelé (€)",
            "charges_reelles": "Charges réelles (€)",
            "ecart": "Écart (€)",
            "ecart_pct": "Écart (%)"
        })
        .assign(**{
            "Appel budget (€)": lambda d: d["Appel budget (€)"].apply(euro),
            "Loi ALUR (5 %) (€)": lambda d: d["Loi ALUR (5 %) (€)"].apply(euro),
            "Total appelé (€)": lambda d: d["Total appelé (€)"].apply(euro),
            "Charges réelles (€)": lambda d: d["Charges réelles (€)"].apply(euro),
            "Écart (€)": lambda d: d["Écart (€)"].apply(euro),
            "Écart (%)": lambda d: d["Écart (%)"].round(2)
        }),
        use_container_width=True
    )

    st.caption(
        "ℹ️ La ligne **Loi ALUR** est calculée automatiquement à 5 % "
        "de l’appel de fonds budget. Elle n’est pas stockée en base."
    )