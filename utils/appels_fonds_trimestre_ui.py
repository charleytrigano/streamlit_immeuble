import streamlit as st
import pandas as pd

BASE_TANTIEMES = 10_000
TAUX_LOI_ALUR = 0.05


def euro(x):
    return f"{x:,.2f} €".replace(",", " ").replace(".", ",")


def appels_fonds_trimestre_ui(supabase, annee):
    st.subheader(f"📢 Appels de fonds trimestriels – {annee}")

    # ==================================================
    # 1. BUDGET ANNUEL
    # ==================================================
    bud = (
        supabase
        .table("budgets")
        .select("budget")
        .eq("annee", annee)
        .execute()
    )

    if not bud.data:
        st.warning("Aucun budget enregistré pour cette année")
        return

    budget_annuel = sum(b["budget"] for b in bud.data)
    budget_trimestriel = budget_annuel / 4

    # ==================================================
    # 2. LOTS
    # ==================================================
    lots = (
        supabase
        .table("lots")
        .select("""
            lot_id,
            lot,
            proprietaire,
            tantiemes
        """)
        .execute()
    )

    if not lots.data:
        st.warning("Aucun lot trouvé")
        return

    df_lots = pd.DataFrame(lots.data)
    df_lots["tantiemes"] = df_lots["tantiemes"].fillna(0)

    # ==================================================
    # 3. CALCUL DES APPELS
    # ==================================================
    df_lots["appel_trimestriel"] = (
        budget_trimestriel * df_lots["tantiemes"] / BASE_TANTIEMES
    )

    df_lots["loi_alur"] = df_lots["appel_trimestriel"] * TAUX_LOI_ALUR
    df_lots["total_appel"] = (
        df_lots["appel_trimestriel"] + df_lots["loi_alur"]
    )

    # ==================================================
    # 4. KPI
    # ==================================================
    col1, col2, col3 = st.columns(3)

    col1.metric(
        "Budget annuel",
        euro(budget_annuel)
    )

    col2.metric(
        "Appel trimestriel total",
        euro(df_lots["appel_trimestriel"].sum())
    )

    col3.metric(
        "Total Loi ALUR (5 %)",
        euro(df_lots["loi_alur"].sum())
    )

    # ==================================================
    # 5. TABLEAU PAR LOT
    # ==================================================
    st.markdown("### 📋 Appels par lot")

    st.dataframe(
        df_lots[[
            "lot",
            "proprietaire",
            "tantiemes",
            "appel_trimestriel",
            "loi_alur",
            "total_appel"
        ]]
        .rename(columns={
            "lot": "Lot",
            "proprietaire": "Propriétaire",
            "tantiemes": "Tantièmes",
            "appel_trimestriel": "Appel trimestriel (€)",
            "loi_alur": "Loi ALUR 5 % (€)",
            "total_appel": "Total à appeler (€)"
        })
        .sort_values("Lot"),
        use_container_width=True
    )

    # ==================================================
    # 6. SYNTHÈSE PAR PROPRIÉTAIRE
    # ==================================================
    st.markdown("### 👤 Synthèse par propriétaire")

    synthese = (
        df_lots
        .groupby("proprietaire", as_index=False)
        .agg(
            appel=("appel_trimestriel", "sum"),
            loi_alur=("loi_alur", "sum"),
            total=("total_appel", "sum")
        )
        .fillna("—")
    )

    st.dataframe(
        synthese.rename(columns={
            "proprietaire": "Propriétaire",
            "appel": "Appel trimestriel (€)",
            "loi_alur": "Loi ALUR (€)",
            "total": "Total (€)"
        }),
        use_container_width=True
    )