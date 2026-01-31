import streamlit as st
import pandas as pd

TAUX_ALUR = 0.05
BASE_TANTIEMES = 10000


def appels_fonds_ui(supabase):
    st.header("📢 Appels de fonds trimestriels")

    # =========================
    # Paramètres
    # =========================
    annee = st.selectbox("Année", [2023, 2024, 2025, 2026], index=2)
    trimestre = st.selectbox("Trimestre", [1, 2, 3, 4], index=0)

    # =========================
    # Budget annuel
    # =========================
    bud_resp = (
        supabase
        .table("budgets")
        .select("budget")
        .eq("annee", annee)
        .execute()
    )

    if not bud_resp.data:
        st.warning("Aucun budget enregistré pour cette année.")
        return

    budget_annuel = sum(b["budget"] for b in bud_resp.data)
    montant_alur = budget_annuel * TAUX_ALUR
    total_a_appeler = budget_annuel + montant_alur
    appel_trimestriel = total_a_appeler / 4

    # =========================
    # Lots
    # =========================
    lots_resp = (
        supabase
        .table("lots")
        .select("lot_id, lot, proprietaire, tantiemes")
        .execute()
    )

    if not lots_resp.data:
        st.warning("Aucun lot trouvé.")
        return

    df_lots = pd.DataFrame(lots_resp.data)

    # Sécurité
    df_lots["tantiemes"] = pd.to_numeric(df_lots["tantiemes"], errors="coerce").fillna(0)

    # =========================
    # Calcul appels par lot
    # =========================
    df_lots["part_lot"] = (
        appel_trimestriel * df_lots["tantiemes"] / BASE_TANTIEMES
    )

    # =========================
    # Tableau par propriétaire
    # =========================
    df_owner = (
        df_lots
        .groupby("proprietaire", as_index=False)
        .agg(
            tantiemes=("tantiemes", "sum"),
            appel=("part_lot", "sum")
        )
    )

    # =========================
    # Affichage KPI
    # =========================
    col1, col2, col3, col4 = st.columns(4)

    col1.metric("Budget annuel", f"{budget_annuel:,.2f} €".replace(",", " "))
    col2.metric("Loi ALUR (5 %)", f"{montant_alur:,.2f} €".replace(",", " "))
    col3.metric("Total annuel", f"{total_a_appeler:,.2f} €".replace(",", " "))
    col4.metric(
        f"Appel T{trimestre}",
        f"{appel_trimestriel:,.2f} €".replace(",", " ")
    )

    # =========================
    # Tableau final
    # =========================
    st.markdown("### 📄 Détail des appels par propriétaire")

    table = df_owner.rename(columns={
        "proprietaire": "Propriétaire",
        "tantiemes": "Tantièmes",
        "appel": f"Appel T{trimestre} (€)"
    })

    # Ligne TOTAL
    total_row = pd.DataFrame([{
        "Propriétaire": "TOTAL",
        "Tantièmes": table["Tantièmes"].sum(),
        f"Appel T{trimestre} (€)": table[f"Appel T{trimestre} (€)"].sum()
    }])

    table = pd.concat([table, total_row], ignore_index=True)

    st.dataframe(table, use_container_width=True)

    # =========================
    # Contrôle
    # =========================
    st.caption(
        "✔ Répartition proportionnelle aux tantièmes — "
        "Budget + Loi ALUR répartis trimestriellement."
    )