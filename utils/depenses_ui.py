import streamlit as st
import pandas as pd
from datetime import date


def depenses_ui(supabase):
    st.title("📋 État des dépenses")

    # =========================
    # Chargement des données
    # =========================
    data = (
        supabase
        .table("depenses")
        .select("*")
        .order("date", desc=True)
        .execute()
        .data
    )

    if not data:
        df = pd.DataFrame()
    else:
        df = pd.DataFrame(data)

    # =========================
    # Sélecteur année
    # =========================
    if not df.empty:
        annees = sorted(df["annee"].dropna().unique().tolist())
    else:
        annees = [date.today().year]

    annee = st.selectbox("Année", annees, index=len(annees) - 1)

    df_annee = df[df["annee"] == annee] if not df.empty else pd.DataFrame()

    # =========================
    # KPI
    # =========================
    col1, col2, col3 = st.columns(3)

    total = df_annee["montant_ttc"].sum() if not df_annee.empty else 0
    nb = len(df_annee)
    moyenne = total / nb if nb > 0 else 0

    col1.metric("Total dépenses (€)", f"{total:,.2f}")
    col2.metric("Nombre de lignes", nb)
    col3.metric("Dépense moyenne (€)", f"{moyenne:,.2f}")

    # =========================
    # Onglets
    # =========================
    tab_consulter, tab_ajouter, tab_modifier, tab_supprimer = st.tabs(
        ["📊 Consulter", "➕ Ajouter", "✏️ Modifier", "🗑 Supprimer"]
    )

    # =========================
    # CONSULTER
    # =========================
    with tab_consulter:
        if df_annee.empty:
            st.info("Aucune dépense pour cette année.")
        else:
            st.dataframe(
                df_annee.sort_values("date", ascending=False),
                use_container_width=True
            )

    # =========================
    # AJOUTER
    # =========================
    with tab_ajouter:
        st.subheader("Ajouter une dépense")

        with st.form("add_depense_form", clear_on_submit=True):
            d = st.date_input("Date", value=date.today())
            compte = st.text_input("Compte")
            poste = st.text_input("Poste")
            fournisseur = st.text_input("Fournisseur")

            montant_saisi = st.number_input(
                "Montant TTC (€)",
                min_value=0.0,
                step=0.01
            )

            type_depense = st.selectbox(
                "Type (optionnel)",
                ["Charge", "Avoir", "Remboursement"]
            )

            lien_facture = st.text_input("Lien facture (optionnel)")
            commentaire = st.text_area("Commentaire (optionnel)")

            submit = st.form_submit_button("💾 Enregistrer")

        if submit:
            # =========================
            # RÈGLE MÉTIER (SIGNATURE)
            # =========================
            if type_depense in ["Avoir", "Remboursement"]:
                montant_final = -abs(montant_saisi)
            else:
                montant_final = abs(montant_saisi)

            payload = {
                "annee": d.year,
                "date": d.isoformat(),
                "compte": compte,
                "poste": poste,
                "fournisseur": fournisseur,
                "montant_ttc": montant_final,
                "type": type_depense,
                "lien_facture": lien_facture or None,
                "commentaire": commentaire or None,
            }

            try:
                supabase.table("depenses").insert(payload).execute()
                st.success("Dépense enregistrée")
                st.rerun()
            except Exception as e:
                st.error("Erreur lors de l’enregistrement")
                st.code(str(e))

    # =========================
    # MODIFIER
    # =========================
    with tab_modifier:
        if df_annee.empty:
            st.info("Aucune dépense à modifier.")
        else:
            id_edit = st.selectbox(
                "Sélectionner une dépense",
                df_annee["id"],
                key="edit_depense"
            )

            row = df_annee[df_annee["id"] == id_edit].iloc[0]

            with st.form("edit_depense_form"):
                d = st.date_input("Date", value=pd.to_datetime(row["date"]))
                compte = st.text_input("Compte", row["compte"])
                poste = st.text_input("Poste", row["poste"])
                fournisseur = st.text_input("Fournisseur", row["fournisseur"])

                montant_abs = abs(float(row["montant_ttc"]))

                type_depense = st.selectbox(
                    "Type",
                    ["Charge", "Avoir", "Remboursement"],
                    index=["Charge", "Avoir", "Remboursement"].index(
                        row.get("type", "Charge")
                    )
                )

                montant_saisi = st.number_input(
                    "Montant TTC (€)",
                    min_value=0.0,
                    value=montant_abs,
                    step=0.01
                )

                submit = st.form_submit_button("💾 Mettre à jour")

            if submit:
                if type_depense in ["Avoir", "Remboursement"]:
                    montant_final = -abs(montant_saisi)
                else:
                    montant_final = abs(montant_saisi)

                supabase.table("depenses").update({
                    "annee": d.year,
                    "date": d.isoformat(),
                    "compte": compte,
                    "poste": poste,
                    "fournisseur": fournisseur,
                    "montant_ttc": montant_final,
                    "type": type_depense,
                }).eq("id", id_edit).execute()

                st.success("Dépense mise à jour")
                st.rerun()

    # =========================
    # SUPPRIMER
    # =========================
    with tab_supprimer:
        if df_annee.empty:
            st.info("Aucune dépense à supprimer.")
        else:
            id_del = st.selectbox(
                "Sélectionner une dépense",
                df_annee["id"],
                key="delete_depense"
            )

            if st.button("🗑 Supprimer définitivement"):
                supabase.table("depenses").delete().eq("id", id_del).execute()
                st.success("Dépense supprimée")
                st.rerun()