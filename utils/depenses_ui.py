import streamlit as st
import pandas as pd
from datetime import date


def depenses_ui(supabase):
    st.title("📋 État des dépenses")

    data = supabase.table("depenses").select("*").execute().data
    df = pd.DataFrame(data) if data else pd.DataFrame()

    annees = sorted(df["annee"].unique()) if not df.empty else [date.today().year]
    annee = st.selectbox("Année", annees, index=len(annees) - 1)

    df_annee = df[df["annee"] == annee] if not df.empty else pd.DataFrame()

    col1, col2, col3 = st.columns(3)
    total = df_annee["montant_ttc"].sum() if not df_annee.empty else 0
    col1.metric("Total dépenses (€)", f"{total:,.2f}")
    col2.metric("Nombre de lignes", len(df_annee))
    col3.metric(
        "Dépense moyenne (€)",
        f"{(total / len(df_annee)) if len(df_annee) else 0:,.2f}"
    )

    tab1, tab2 = st.tabs(["📊 Consulter", "➕ Ajouter"])

    # =====================
    # CONSULTER
    # =====================
    with tab1:
        st.dataframe(df_annee, use_container_width=True)

    # =====================
    # AJOUTER
    # =====================
    with tab2:
        with st.form("add_depense"):
            d = st.date_input("Date", value=date.today())
            compte = st.text_input("Compte")
            poste = st.text_input("Poste")
            fournisseur = st.text_input("Fournisseur")

            montant = st.number_input(
                "Montant TTC (€)",
                step=0.01,
                format="%.2f"
            )

            type_depense = st.selectbox(
                "Type",
                ["Charge", "Avoir", "Remboursement"]
            )

            submit = st.form_submit_button("Enregistrer")

        if submit:
            montant_final = (
                -abs(montant)
                if type_depense in ["Avoir", "Remboursement"]
                else abs(montant)
            )

            payload = {
                "annee": d.year,
                "date": d.isoformat(),
                "compte": compte,
                "poste": poste,
                "fournisseur": fournisseur,
                "montant_ttc": montant_final,
                "type": type_depense,
            }

            supabase.table("depenses").insert(payload).execute()
            st.success("Dépense enregistrée")
            st.rerun()