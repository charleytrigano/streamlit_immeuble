import streamlit as st
import pandas as pd


def appels_fonds_trimestre_ui(supabase, annee):
    st.subheader(f"📢 Appels de fonds par trimestre – année {annee}")

    # =========================
    # RÉCUPÉRATION DU BUDGET ANNUEL
    # =========================
    try:
        res = (
            supabase
            .table("budgets")
            .select("montant")
            .eq("annee", annee)
            .execute()
        )
    except Exception as e:
        st.error("Erreur lors de la récupération du budget")
        st.exception(e)
        return

    if not res.data:
        st.warning("Aucun budget trouvé pour cette année.")
        return

    df_budget = pd.DataFrame(res.data)

    if "montant" not in df_budget.columns:
        st.error("La colonne 'montant' est introuvable dans la table budgets.")
        return

    budget_annuel = df_budget["montant"].sum()

    # =========================
    # CALCUL DES APPELS
    # =========================
    appel_trimestriel = budget_annuel / 4
    alur_trimestriel = appel_trimestriel * 0.05

    # =========================
    # CONSTRUCTION DU TABLEAU
    # =========================
    data = []

    for trimestre in ["T1", "T2", "T3", "T4"]:
        data.append({
            "Trimestre": trimestre,
            "Libellé": "Appel de fonds",
            "Montant (€)": round(appel_trimestriel, 2)
        })
        data.append({
            "Trimestre": trimestre,
            "Libellé": "Loi ALUR (5 %)",
            "Montant (€)": round(alur_trimestriel, 2)
        })

    df_appels = pd.DataFrame(data)

    # =========================
    # AFFICHAGE
    # =========================
    st.success("Module Appels de fonds chargé correctement ✅")

    st.metric(
        label="Budget annuel",
        value=f"{budget_annuel:,.2f} €".replace(",", " ").replace(".", ",")
    )

    st.dataframe(
        df_appels,
        use_container_width=True,
        hide_index=True
    )

    # =========================
    # TOTAUX DE CONTRÔLE
    # =========================
    total_appels = appel_trimestriel * 4
    total_alur = alur_trimestriel * 4

    col1, col2, col3 = st.columns(3)

    col1.metric(
        "Total appels de fonds",
        f"{total_appels:,.2f} €".replace(",", " ").replace(".", ",")
    )

    col2.metric(
        "Total Loi ALUR",
        f"{total_alur:,.2f} €".replace(",", " ").replace(".", ",")
    )

    col3.metric(
        "Total global",
        f"{(total_appels + total_alur):,.2f} €".replace(",", " ").replace(".", ",")
    )