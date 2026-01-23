from supabase import Client
import streamlit as st
import uuid


def upload_facture(supabase: Client, file, annee, depense_id):
    path = f"{annee}/{depense_id}.pdf"

    supabase.storage.from_("factures").upload(
        path,
        file.getvalue(),
        {"content-type": "application/pdf"},
        upsert=True
    )

    public_url = supabase.storage.from_("factures").get_public_url(path)
    return public_url


# =========================
# ➕ Ajouter une dépense
# =========================
if onglet == "➕ Ajouter":
    with st.form("add_depense"):
        date = st.date_input("Date")
        compte = st.text_input("Compte")
        poste = st.text_input("Poste")
        fournisseur = st.text_input("Fournisseur")
        montant = st.number_input("Montant TTC (€)", step=0.01)
        type_dep = st.selectbox("Type", ["Charge", "Avoir", "Remboursement"])
        facture = st.file_uploader("Facture (PDF)", type=["pdf"])

        submit = st.form_submit_button("Enregistrer")

    if submit:
        depense_id = str(uuid.uuid4())

        payload = {
            "id": depense_id,
            "annee": date.year,
            "date": str(date),
            "compte": compte,
            "poste": poste,
            "fournisseur": fournisseur,
            "montant_ttc": montant,
            "type": type_dep,
        }

        supabase.table("depenses").insert(payload).execute()

        if facture:
            url = upload_facture(
                supabase,
                facture,
                date.year,
                depense_id
            )

            supabase.table("depenses").update(
                {"lien_facture": url}
            ).eq("id", depense_id).execute()

        st.success("Dépense enregistrée avec facture")