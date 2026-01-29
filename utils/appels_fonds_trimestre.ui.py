import streamlit as st
import pandas as pd


def euro(x):
    return f"{x:,.2f} €".replace(",", " ").replace(".", ",")


def appels_fonds_trimestre_ui(supabase, annee):
    st.header("📢 Appels de fonds – par trimestre")

    # =========================
    # CHARGEMENT BUDGET
    # =========================
    bud_resp = (
        supabase
        .table("budgets")
        .select("groupe_compte, libelle_groupe, budget")
        .eq("annee", annee)
        .execute()
    )

    df_bud = pd.DataFrame(bud_resp.data)

    if df_bud.empty:
        st.warning("Aucun budget enregistré pour cette année.")
        return

    # =========================
    # TOTAL BUDGET
    # =========================
    budget_total = df_bud["budget"].sum()

    # =========================
    # CALCUL TRIMESTRES
    # =========================
    trimestres = pd.DataFrame({
        "Trimestre": ["T1", "T2", "T3", "T4"],
        "Montant": [budget_total / 4] * 4
    })

    # =========================
    # LOI ALUR (5 %)
    # =========================
    loi_alur = budget_total * 0.05

    # =========================
    # KPI
    # =========================
    col1, col2, col3 = st.columns(3)

    col1.metric("Budget annuel", euro(budget_total))
    col2.metric("Appel trimestriel", euro(budget_total / 4))
    col3.metric("Fonds Loi ALUR (5 %)", euro(loi_alur))

    st.divider()

    # =========================
    # TABLEAU APPELS
    # =========================
    st.subheader("📅 Appels de fonds par trimestre")

    st.dataframe(
        trimestres.assign(
            **{"Montant (€)": trimestres["Montant"].apply(euro)}
        )[["Trimestre", "Montant (€)"]],
        use_container_width=True
    )

    # =========================
    # LIGNE LOI ALUR
    # =========================
    st.subheader("⚖️ Fonds Loi ALUR")

    st.dataframe(
        pd.DataFrame([{
            "Libellé": "Fonds Loi ALUR (5 %)",
            "Montant (€)": euro(loi_alur)
        }]),
        use_container_width=True
    )