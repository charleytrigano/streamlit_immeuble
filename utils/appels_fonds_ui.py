import streamlit as st
import pandas as pd

def appels_fonds_ui(supabase, annee):
    st.header("💸 Appels de fonds")

    # =========================
    # 1. Chargement du budget
    # =========================
    res = (
        supabase
        .table("budgets")
        .select("montant")
        .eq("annee", annee)
        .execute()
    )

    if not res.data:
        st.warning("Aucun budget défini pour cette année.")
        return

    df_budget = pd.DataFrame(res.data)

    budget_total = df_budget["montant"].sum()

    # =========================
    # 2. Calcul Loi Alur (5 %)
    # =========================
    loi_alur = round(budget_total * 0.05, 2)

    # =========================
    # 3. Construction tableau
    # =========================
    df_appels = pd.DataFrame([
        {
            "Libellé": "Appel de fonds – Budget",
            "Montant (€)": budget_total
        },
        {
            "Libellé": "Loi Alur (5 %)",
            "Montant (€)": loi_alur
        },
        {
            "Libellé": "Total à appeler",
            "Montant (€)": budget_total + loi_alur
        }
    ])

    # =========================
    # 4. Affichage
    # =========================
    st.subheader(f"📅 Année {annee}")

    st.dataframe(
        df_appels,
        use_container_width=True,
        hide_index=True
    )

    st.info(
        "ℹ️ La ligne **Loi Alur** est calculée automatiquement à hauteur de **5 %** "
        "de l’appel de fonds basé sur le budget annuel."
    )