import streamlit as st
import pandas as pd


COMPTES_4_CHIFFRES = {"6211", "6213", "6222", "6223"}


def cle_budget(compte: str) -> str:
    compte = str(compte)
    if compte[:4] in COMPTES_4_CHIFFRES:
        return compte[:4]
    return compte[:3]


def budget_vs_reel_ui(supabase):
    st.title("📊 Budget vs Réel")

    # =====================
    # Année
    # =====================
    annee = st.selectbox("Année", [2023, 2024, 2025, 2026], index=2)

    # =====================
    # Chargement données
    # =====================
    dep_rows = (
        supabase.table("depenses")
        .select("annee, compte, montant_ttc")
        .eq("annee", annee)
        .execute()
        .data
    )

    bud_rows = (
        supabase.table("budget")
        .select("annee, compte, budget")
        .eq("annee", annee)
        .execute()
        .data
    )

    if not dep_rows or not bud_rows:
        st.warning("Données budget ou dépenses manquantes pour cette année")
        return

    df_dep = pd.DataFrame(dep_rows)
    df_bud = pd.DataFrame(bud_rows)

    # =====================
    # Normalisation clés
    # =====================
    df_dep["cle"] = df_dep["compte"].apply(cle_budget)
    df_bud["cle"] = df_bud["compte"].apply(cle_budget)

    # =====================
    # Agrégation
    # =====================
    dep_agg = (
        df_dep.groupby("cle", as_index=False)["montant_ttc"]
        .sum()
        .rename(columns={"montant_ttc": "reel"})
    )

    bud_agg = (
        df_bud.groupby("cle", as_index=False)["budget"]
        .sum()
    )

    # =====================
    # Jointure
    # =====================
    comp = bud_agg.merge(dep_agg, on="cle", how="left")
    comp["reel"] = comp["reel"].fillna(0)

    comp["ecart_eur"] = comp["reel"] - comp["budget"]
    comp["ecart_pct"] = comp.apply(
        lambda r: (r["ecart_eur"] / r["budget"] * 100)
        if r["budget"] != 0 else 0,
        axis=1,
    )

    # =====================
    # KPIs
    # =====================
    total_budget = comp["budget"].sum()
    total_reel = comp["reel"].sum()
    total_ecart = total_reel - total_budget
    taux = (total_ecart / total_budget * 100) if total_budget else 0

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Budget (€)", f"{total_budget:,.2f}")
    c2.metric("Réel (€)", f"{total_reel:,.2f}")
    c3.metric("Écart (€)", f"{total_ecart:,.2f}")
    c4.metric("Écart (%)", f"{taux:.1f} %")

    # =====================
    # Tableau
    # =====================
    st.dataframe(
        comp.sort_values("cle"),
        use_container_width=True,
    )

    # =====================
    # Drill-down
    # =====================
    st.subheader("🔎 Détail par compte")

    cle_sel = st.selectbox(
        "Groupe de compte",
        comp["cle"].sort_values(),
    )

    df_detail = df_dep[df_dep["cle"] == cle_sel]

    if df_detail.empty:
        st.info("Aucune dépense pour ce groupe")
    else:
        st.dataframe(
            df_detail[["compte", "montant_ttc"]],
            use_container_width=True,
        )