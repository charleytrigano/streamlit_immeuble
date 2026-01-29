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
            .select("budget")
            .eq("annee", annee)
            .execute()
        )
    except Exception as e:
        st.error("❌ Erreur Supabase (lecture budgets)")
        st.exception(e)
        return

    if not res.data:
        st.warning("Aucun budget trouvé pour cette année.")
        return

    df_budget = pd.DataFrame(res.data)

    if "budget" not in df_budget.columns:
        st.error("Colonne 'budget' introuvable dans la table budgets.")
        st.stop()

    # =========================
    # CALCULS
    # =========================
    budget_annuel = df_budget["budget"].sum()

    appel_trimestriel = budget_annuel / 4
    alur_trimestriel = appel_trimestriel * 0.05

    # =========================
    # TABLEAU DES APPELS
    # =========================
    rows = []
    for trimestre in ["T1", "T2", "T3", "T4"]:
        rows.append({
            "Trimestre": trimestre,
            "Libellé": "Appel de fonds",
            "Montant (€)": round(appel_trimestriel, 2)
        })
        rows.append({
            "Trimestre": trimestre,
            "Libellé": "Loi ALUR (5 %)",
            "Montant (€)": round(alur_trimestriel, 2)
        })

    df = pd.DataFrame(rows)

    # =========================
    # AFFICHAGE
    # =========================
    st.success("Module Appels de fonds par trimestre chargé correctement ✅")

    st.metric(
        "Budget annuel",
        f"{budget_annuel:,.2f} €".replace(",", " ").replace(".", ",")
    )

    st.dataframe(df, use_container_width=True, hide_index=True)

    # =========================
    # TOTAUX
    # =========================
    col1, col2, col3 = st.columns(3)

    col1.metric(
        "Total appels",
        f"{budget_annuel:,.2f} €".replace(",", " ").replace(".", ",")
    )

    col2.metric(
        "Total Loi ALUR",
        f"{(alur_trimestriel * 4):,.2f} €".replace(",", " ").replace(".", ",")
    )

    col3.metric(
        "Total global",
        f"{(budget_annuel + alur_trimestriel * 4):,.2f} €".replace(",", " ").replace(".", ",")
    )