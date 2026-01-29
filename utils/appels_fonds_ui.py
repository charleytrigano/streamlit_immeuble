import streamlit as st
import pandas as pd

def appels_fonds_ui(supabase, annee):
    st.header("📢 Appels de fonds")

    # =========================
    # RÉCUPÉRATION DU BUDGET
    # =========================
    res = (
        supabase
        .table("budgets")
        .select("budget")
        .eq("annee", annee)
        .execute()
    )

    data = res.data or []

    if not data:
        st.warning("Aucun budget trouvé pour cette année.")
        return

    df_budget = pd.DataFrame(data)

    if "budget" not in df_budget.columns:
        st.error("❌ Colonne 'budget' introuvable dans la table budgets.")
        return

    budget_total = float(df_budget["budget"].sum())

    # =========================
    # CALCUL LOI ALUR (5 %)
    # =========================
    loi_alur = round(budget_total * 0.05, 2)
    total_appels = budget_total + loi_alur

    # =========================
    # TABLEAU RÉCAPITULATIF
    # =========================
    df_appels = pd.DataFrame([
        {"Type": "Budget annuel", "Montant (€)": budget_total},
        {"Type": "Loi ALUR (5 %)", "Montant (€)": loi_alur},
        {"Type": "Total appels de fonds", "Montant (€)": total_appels},
    ])

    st.subheader(f"📅 Année {annee}")
    st.dataframe(
        df_appels.style.format({"Montant (€)": "{:,.2f} €"}),
        use_container_width=True
    )

    # =========================
    # KPI
    # =========================
    c1, c2, c3 = st.columns(3)

    c1.metric("Budget", f"{budget_total:,.2f} €")
    c2.metric("Loi ALUR (5 %)", f"{loi_alur:,.2f} €")
    c3.metric("Total à appeler", f"{total_appels:,.2f} €")

    st.success("Module Appels de fonds chargé correctement ✅")