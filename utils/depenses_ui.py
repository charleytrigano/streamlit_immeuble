import streamlit as st
import pandas as pd
from datetime import date
import uuid

def depenses_ui(supabase):
    st.title("📋 État des dépenses")

    # =====================
    # Sélection année
    # =====================
    annee = st.selectbox("Année", [2023, 2024, 2025, 2026], index=2)

    # =====================
    # Lecture des dépenses
    # =====================
    data = (
        supabase.table("depenses")
        .select("*")
        .eq("annee", annee)
        .execute()
        .data
    )

    df = pd.DataFrame(data) if data else pd.DataFrame()

    # =====================
    # KPIs
    # =====================
    total = df["montant_ttc"].sum() if not df.empty else 0
    count = len(df)
    moyenne = total / count if count else 0

    col1, col2, col3 = st.columns(3)
    col1.metric("Total dépenses (€)", f"{total:,.2f}")
    col2.metric("Nombre de lignes", count)
    col3.metric("Dépense moyenne (€)", f"{moyenne:,.2f}")

    # =====================
    # Navigation
    # =====================
    tab_consult, tab_add = st.tabs(["📊 Consulter", "➕ Ajouter"])

    # =====================
    # CONSULTER
    # =====================
    with tab_consult:
        if df.empty:
            st.info("Aucune dépense")
        else:
            st.dataframe(
                df[[
                    "date",
                    "compte",
                    "poste",
                    "fournisseur",
                    "montant_ttc",
                    "type",
                    "pdf_url"
                ]],
                use_container_width=True
            )

    # =====================
    # AJOUTER
    # =====================
    with tab_add:
        st.subheader("Ajouter une dépense")

        with st.form("add_depense"):
            d_date = st.date_input("Date", value=date.today())
            compte = st.text_input("Compte")
            poste = st.text_input("Poste")
            fournisseur = st.text_input("Fournisseur")
            montant = st.number_input("Montant TTC (€)", step=0.01)
            type_dep = st.selectbox("Type", ["Charge", "Remboursement", "Avoir"])
            pdf = st.file_uploader("Facture PDF", type=["pdf"])
            commentaire = st.text_area("Commentaire (optionnel)")

            submitted = st.form_submit_button("Enregistrer")

        if submitted:
            depense_id = str(uuid.uuid4())

            pdf_url = None

            if pdf:
                path = f"{annee}/{depense_id}.pdf"
                supabase.storage.from_("factures").upload(
                    path,
                    pdf,
                    {"content-type": "application/pdf"}
                )
                pdf_url = supabase.storage.from_("factures").get_public_url(path)

            payload = {
                "id": depense_id,
                "annee": annee,
                "date": str(d_date),
                "compte": compte,
                "poste": poste,
                "fournisseur": fournisseur,
                "montant_ttc": montant,
                "type": type_dep,
                "pdf_url": pdf_url,
                "commentaire": commentaire
            }

            supabase.table("depenses").insert(payload).execute()
            st.success("Dépense enregistrée avec facture liée")
            st.rerun()