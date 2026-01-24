import streamlit as st
import pandas as pd
from datetime import date
import uuid


TYPES = ["Charge", "Remboursement", "Avoir"]


def depenses_ui(supabase):
    st.title("📋 État des dépenses")

    # =====================
    # Année
    # =====================
    annee = st.selectbox("Année", [2023, 2024, 2025, 2026], index=2)

    # =====================
    # Chargement des dépenses
    # =====================
    rows = (
        supabase.table("depenses")
        .select("*")
        .eq("annee", annee)
        .order("date", desc=True)
        .execute()
        .data
    )

    df = pd.DataFrame(rows) if rows else pd.DataFrame()

    # =====================
    # KPIs
    # =====================
    total = df["montant_ttc"].sum() if not df.empty else 0
    count = len(df)
    moyenne = total / count if count else 0

    c1, c2, c3 = st.columns(3)
    c1.metric("Total dépenses (€)", f"{total:,.2f}")
    c2.metric("Nombre de lignes", count)
    c3.metric("Dépense moyenne (€)", f"{moyenne:,.2f}")

    # =====================
    # Onglets
    # =====================
    tab_consult, tab_add, tab_edit, tab_delete = st.tabs(
        ["📊 Consulter", "➕ Ajouter", "✏️ Modifier", "🗑 Supprimer"]
    )

    # =====================
    # CONSULTER
    # =====================
    with tab_consult:
        if df.empty:
            st.info("Aucune dépense")
        else:
            df_view = df.copy()
            if "pdf_url" in df_view.columns:
                df_view["facture"] = df_view["pdf_url"].apply(
                    lambda x: f"[📄 Voir]({x})" if x else ""
                )

            st.dataframe(
                df_view[
                    [
                        "date",
                        "compte",
                        "poste",
                        "fournisseur",
                        "montant_ttc",
                        "type",
                        "facture",
                    ]
                ],
                use_container_width=True,
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
            type_dep = st.selectbox("Type", TYPES)
            pdf = st.file_uploader("Facture PDF", type=["pdf"])
            commentaire = st.text_area("Commentaire (optionnel)")

            submit = st.form_submit_button("Enregistrer")

        if submit:
            depense_id = str(uuid.uuid4())
            pdf_url = None

            if pdf:
                path = f"{annee}/{depense_id}.pdf"
                supabase.storage.from_("factures").upload(
                    path,
                    pdf,
                    {"content-type": "application/pdf"},
                )
                pdf_url = supabase.storage.from_("factures").get_public_url(path)

            supabase.table("depenses").insert(
                {
                    "id": depense_id,
                    "annee": annee,
                    "date": str(d_date),
                    "compte": compte,
                    "poste": poste,
                    "fournisseur": fournisseur,
                    "montant_ttc": montant,
                    "type": type_dep,
                    "pdf_url": pdf_url,
                    "commentaire": commentaire,
                }
            ).execute()

            st.success("Dépense ajoutée")
            st.rerun()

    # =====================
    # MODIFIER
    # =====================
    with tab_edit:
        if df.empty:
            st.info("Aucune dépense à modifier")
        else:
            dep_id = st.selectbox(
                "Sélectionner une dépense",
                df["id"],
                format_func=lambda x: (
                    f"{df[df['id']==x]['date'].iloc[0]} | "
                    f"{df[df['id']==x]['fournisseur'].iloc[0]} | "
                    f"{df[df['id']==x]['montant_ttc'].iloc[0]:,.2f} €"
                ),
            )

            dep = df[df["id"] == dep_id].iloc[0]

            type_value = (
                dep["type"] if dep["type"] in TYPES else "Charge"
            )

            with st.form("edit_depense"):
                d_date = st.date_input("Date", value=pd.to_datetime(dep["date"]))
                compte = st.text_input("Compte", dep["compte"])
                poste = st.text_input("Poste", dep["poste"])
                fournisseur = st.text_input("Fournisseur", dep["fournisseur"])
                montant = st.number_input(
                    "Montant TTC (€)",
                    value=float(dep["montant_ttc"]),
                    step=0.01,
                )
                type_dep = st.selectbox(
                    "Type",
                    TYPES,
                    index=TYPES.index(type_value),
                )
                pdf = st.file_uploader(
                    "Remplacer la facture (optionnel)", type=["pdf"]
                )
                commentaire = st.text_area(
                    "Commentaire", dep.get("commentaire") or ""
                )

                submit_edit = st.form_submit_button("Mettre à jour")

            if submit_edit:
                pdf_url = dep["pdf_url"]

                if pdf:
                    path = f"{annee}/{dep_id}.pdf"
                    supabase.storage.from_("factures").upload(
                        path,
                        pdf,
                        {"content-type": "application/pdf"},
                        upsert=True,
                    )
                    pdf_url = supabase.storage.from_("factures").get_public_url(path)

                supabase.table("depenses").update(
                    {
                        "date": str(d_date),
                        "compte": compte,
                        "poste": poste,
                        "fournisseur": fournisseur,
                        "montant_ttc": montant,
                        "type": type_dep,
                        "pdf_url": pdf_url,
                        "commentaire": commentaire,
                    }
                ).eq("id", dep_id).execute()

                st.success("Dépense mise à jour")
                st.rerun()

    # =====================
    # SUPPRIMER
    # =====================
    with tab_delete:
        if df.empty:
            st.info("Aucune dépense à supprimer")
        else:
            dep_id = st.selectbox(
                "Sélectionner une dépense à supprimer",
                df["id"],
                format_func=lambda x: (
                    f"{df[df['id']==x]['date'].iloc[0]} | "
                    f"{df[df['id']==x]['fournisseur'].iloc[0]} | "
                    f"{df[df['id']==x]['montant_ttc'].iloc[0]:,.2f} €"
                ),
                key="delete_id",
            )

            if st.button("❌ Supprimer définitivement"):
                supabase.storage.from_("factures").remove(
                    [f"{annee}/{dep_id}.pdf"]
                )
                supabase.table("depenses").delete().eq("id", dep_id).execute()

                st.success("Dépense supprimée")
                st.rerun()