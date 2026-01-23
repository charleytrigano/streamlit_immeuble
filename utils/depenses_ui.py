import streamlit as st
import pandas as pd
from datetime import date


def depenses_ui(supabase):
    st.title("📋 État des dépenses")

    # =========================
    # CHARGEMENT DES DONNÉES
    # =========================
    rows = supabase.table("depenses").select("*").execute().data
    df = pd.DataFrame(rows) if rows else pd.DataFrame()

    if df.empty:
        annees = [date.today().year]
    else:
        annees = sorted(df["annee"].unique())

    annee = st.selectbox("Année", annees, index=len(annees) - 1)

    df_annee = df[df["annee"] == annee] if not df.empty else pd.DataFrame()

    # =========================
    # KPI
    # =========================
    total = df_annee["montant_ttc"].sum() if not df_annee.empty else 0
    nb = len(df_annee)
    moy = total / nb if nb else 0

    c1, c2, c3 = st.columns(3)
    c1.metric("Total dépenses (€)", f"{total:,.2f}")
    c2.metric("Nombre de lignes", nb)
    c3.metric("Dépense moyenne (€)", f"{moy:,.2f}")

    # =========================
    # ONGLET
    # =========================
    tab_consulter, tab_ajouter, tab_modifier, tab_supprimer = st.tabs(
        ["📊 Consulter", "➕ Ajouter", "✏️ Modifier", "🗑 Supprimer"]
    )

    # =========================
    # CONSULTER
    # =========================
    with tab_consulter:
        st.dataframe(df_annee, use_container_width=True)

    # =========================
    # AJOUTER
    # =========================
    with tab_ajouter:
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

    # =========================
    # MODIFIER
    # =========================
    with tab_modifier:
        if df_annee.empty:
            st.info("Aucune dépense à modifier")
        else:
            ids = df_annee["id"].tolist()
            dep_id = st.selectbox(
                "Sélectionner une dépense",
                ids,
                key="mod_select"
            )

            dep = df_annee[df_annee["id"] == dep_id].iloc[0]

            with st.form("edit_depense"):
                new_date = st.date_input("Date", value=pd.to_datetime(dep["date"]))
                new_compte = st.text_input("Compte", dep["compte"])
                new_poste = st.text_input("Poste", dep["poste"])
                new_fournisseur = st.text_input("Fournisseur", dep["fournisseur"])

                new_montant = st.number_input(
                    "Montant TTC (€)",
                    value=float(dep["montant_ttc"]),
                    step=0.01,
                    format="%.2f"
                )

                new_type = st.selectbox(
                    "Type",
                    ["Charge", "Avoir", "Remboursement"],
                    index=["Charge", "Avoir", "Remboursement"].index(dep["type"])
                )

                save = st.form_submit_button("Mettre à jour")

            if save:
                supabase.table("depenses").update({
                    "date": new_date.isoformat(),
                    "annee": new_date.year,
                    "compte": new_compte,
                    "poste": new_poste,
                    "fournisseur": new_fournisseur,
                    "montant_ttc": new_montant,
                    "type": new_type,
                }).eq("id", dep_id).execute()

                st.success("Dépense modifiée")
                st.rerun()

    # =========================
    # SUPPRIMER
    # =========================
    with tab_supprimer:
        if df_annee.empty:
            st.info("Aucune dépense à supprimer")
        else:
            del_id = st.selectbox(
                "Sélectionner une dépense",
                df_annee["id"],
                key="del_select"
            )

            if st.button("Supprimer définitivement"):
                supabase.table("depenses").delete().eq("id", del_id).execute()
                st.success("Dépense supprimée")
                st.rerun()