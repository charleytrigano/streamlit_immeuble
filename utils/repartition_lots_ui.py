import streamlit as st
import pandas as pd

BASE_TANTIEMES = 10_000


def repartition_lots_ui(supabase, annee):
    st.header("🏢 Répartition des appels de fonds par lot")

    # =========================
    # BUDGET TOTAL
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
    total_appels = budget_total + loi_alur

    # =========================
    # LOTS
    # =========================
    lots_res = (
        supabase
        .table("lots")
        .select(
            "lot_id, lot, tantiemes, proprietaire, locataire, usage, etage"
        )
        .execute()
    )

    if not lots_res.data:
        st.warning("Aucun lot trouvé.")
        return

    df_lots = pd.DataFrame(lots_res.data)

    if "tantiemes" not in df_lots.columns:
        st.error("Colonne 'tantiemes' manquante dans la table lots.")
        return

    total_tantiemes = df_lots["tantiemes"].sum()

    if total_tantiemes == 0:
        st.error("Total des tantièmes = 0. Impossible de répartir.")
        return

    # =========================
    # CALCUL RÉPARTITION
    # =========================
    df_lots["appel_fonds"] = (
        total_appels * df_lots["tantiemes"] / total_tantiemes
    ).round(2)

    # =========================
    # KPI
    # =========================
    c1, c2, c3 = st.columns(3)

    c1.metric("Budget", f"{budget_total:,.2f} €")
    c2.metric("Loi ALUR (5 %)", f"{loi_alur:,.2f} €")
    c3.metric("Total appels", f"{total_appels:,.2f} €")

    st.divider()

    # =========================
    # TABLEAU FINAL
    # =========================
    df_aff = df_lots[
        [
            "lot",
            "tantiemes",
            "appel_fonds",
            "proprietaire",
            "locataire",
            "usage",
            "etage",
        ]
    ].sort_values("lot")

    st.dataframe(
        df_aff.style.format({
            "appel_fonds": "{:,.2f} €"
        }),
        use_container_width=True
    )

    st.success("Répartition des appels de fonds calculée correctement ✅")