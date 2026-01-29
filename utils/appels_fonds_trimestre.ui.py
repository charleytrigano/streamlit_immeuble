
import streamlit as st
import pandas as pd

BASE_TANTIEMES = 10_000
TRIMESTRES = ["T1", "T2", "T3", "T4"]


def appels_fonds_trimestre_ui(supabase, annee):
    st.header("📢 Appels de fonds par trimestre")

    # =========================
    # BUDGET
    # =========================
    bud_res = (
        supabase
        .table("budgets")
        .select("budget")
        .eq("annee", annee)
        .execute()
    )

    if not bud_res.data:
        st.warning("Aucun budget trouvé pour cette année.")
        return

    df_budget = pd.DataFrame(bud_res.data)
    budget_total = float(df_budget["budget"].sum())

    loi_alur = round(budget_total * 0.05, 2)
    total_annuel = budget_total + loi_alur
    total_trimestre = round(total_annuel / 4, 2)

    # =========================
    # LOTS
    # =========================
    lots_res = (
        supabase
        .table("lots")
        .select(
            "lot_id, lot, tantiemes, proprietaire, locataire"
        )
        .execute()
    )

    if not lots_res.data:
        st.warning("Aucun lot trouvé.")
        return

    df_lots = pd.DataFrame(lots_res.data)

    total_tantiemes = df_lots["tantiemes"].sum()
    if total_tantiemes == 0:
        st.error("Total tantièmes = 0")
        return

    # =========================
    # CALCUL PAR LOT
    # =========================
    df_lots["appel_annuel"] = (
        total_annuel * df_lots["tantiemes"] / total_tantiemes
    ).round(2)

    df_lots["appel_trimestriel"] = (
        df_lots["appel_annuel"] / 4
    ).round(2)

    # =========================
    # KPI
    # =========================
    c1, c2, c3, c4 = st.columns(4)

    c1.metric("Budget", f"{budget_total:,.2f} €")
    c2.metric("Loi ALUR (5 %)", f"{loi_alur:,.2f} €")
    c3.metric("Total annuel", f"{total_annuel:,.2f} €")
    c4.metric("Par trimestre", f"{total_trimestre:,.2f} €")

    st.divider()

    # =========================
    # TABLEAU PAR LOT
    # =========================
    st.subheader("📋 Appels trimestriels par lot")

    df_aff = df_lots[
        [
            "lot",
            "tantiemes",
            "appel_trimestriel",
            "proprietaire",
            "locataire"
        ]
    ].sort_values("lot")

    st.dataframe(
        df_aff.style.format({
            "appel_trimestriel": "{:,.2f} €"
        }),
        use_container_width=True
    )

    # =========================
    # TABLEAU DÉTAILLÉ LOT × TRIMESTRE
    # =========================
    st.subheader("📆 Détail par trimestre")

    rows = []
    for _, r in df_lots.iterrows():
        for t in TRIMESTRES:
            rows.append({
                "Lot": r["lot"],
                "Trimestre": t,
                "Montant": r["appel_trimestriel"]
            })

    df_trim = pd.DataFrame(rows)

    st.dataframe(
        df_trim.style.format({
            "Montant": "{:,.2f} €"
        }),
        use_container_width=True
    )

    st.success("Appels de fonds trimestriels calculés correctement ✅")