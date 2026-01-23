import streamlit as st
import pandas as pd
from datetime import datetime


def depenses_ui(supabase):
    st.header("📋 État des dépenses")

    # =========================
    # 1. CHARGEMENT DES DONNÉES
    # =========================
    resp = supabase.table("depenses").select("*").execute()
    data = resp.data if resp.data else []
    df = pd.DataFrame(data)

    if not df.empty:
        df["annee"] = df["annee"].astype(int)
        df["montant_ttc"] = df["montant_ttc"].astype(float)
        df["date"] = pd.to_datetime(df["date"])

    # =========================
    # 2. FILTRE ANNÉE (LIBRE)
    # =========================
    current_year = datetime.now().year

    annee = st.number_input(
        "Année",
        min_value=2000,
        max_value=current_year + 10,
        value=current_year,
        step=1
    )

    df_annee = df[df["annee"] == annee] if not df.empty else pd.DataFrame()

    # =========================
    # 3. KPI
    # =========================
    total = df_annee["montant_ttc"].sum() if not df_annee.empty else 0
    nb = len(df_annee)
    moyenne = total / nb if nb else 0

    col1, col2, col3 = st.columns(3)
    col1.metric("Total dépenses (€)", f"{total:,.2f}")
    col2.metric("Nombre de lignes", nb)
    col3.metric("Dépense moyenne (€)", f"{moyenne:,.2f}")

    # =========================
    # 4. ONGLETS
    # =========================
    tab_consult, tab_add, tab_edit, tab_delete = st.tabs(
        ["📊 Consulter", "➕ Ajouter", "✏️ Modifier", "🗑 Supprimer"]
    )

    # =========================
    # 5. CONSULTER
    # =========================
    with tab_consult:
        if df_annee.empty:
            st.info("Aucune dépense pour cette année.")
        else:
            st.dataframe(
                df_annee.sort_values("date", ascending=False),
                use_container_width=True
            )

    # =========================
    # 6. AJOUTER (CORRIGÉ)
    # =========================
    with tab_add:
        st.subheader("Ajouter une dépense")

        with st.form("add_depense"):
            date_depense = st.date_input("Date")
            compte = st.text_input("Compte")
            poste = st.text_input("Poste")
            fournisseur = st.text_input("Fournisseur")
            montant = st.number_input("Montant TTC (€)", min_value=0.0, step=10.0)
            lien = st.text_input("Lien facture (optionnel)")
            type_dep = st.text_input("Type (optionnel)")

            submit = st.form_submit_button("💾 Enregistrer")

        if submit:
            if not compte or not poste:
                st.error("Compte et poste sont obligatoires.")
            else:
                payload = {
                    "annee": date_depense.year,
                    "date": date_depense.isoformat(),  # ✅ CORRECTION CRITIQUE
                    "compte": compte,
                    "poste": poste,
                    "fournisseur": fournisseur,
                    "montant_ttc": float(montant),
                    "piece": lien or None,
                    "type": type_dep or None,
                }

                try:
                    supabase.table("depenses").insert(payload).execute()
                    st.success("Dépense ajoutée avec succès.")
                    st.rerun()
                except Exception as e:
                    st.error("Erreur lors de l'ajout de la dépense.")
                    st.exception(e)

    # =========================
    # 7. MODIFIER
    # =========================
    with tab_edit:
        st.subheader("Modifier une dépense")

        if df_annee.empty:
            st.info("Aucune dépense à modifier.")
        else:
            id_sel = st.selectbox("Sélectionner", df_annee["id"])
            row = df_annee[df_annee["id"] == id_sel].iloc[0]

            with st.form("edit_depense"):
                date_dep = st.date_input("Date", row["date"].date())
                compte = st.text_input("Compte", row["compte"])
                poste = st.text_input("Poste", row["poste"])
                fournisseur = st.text_input("Fournisseur", row["fournisseur"])
                montant = st.number_input("Montant TTC (€)", value=float(row["montant_ttc"]))
                submit_edit = st.form_submit_button("✏️ Mettre à jour")

            if submit_edit:
                supabase.table("depenses").update({
                    "date": date_dep.isoformat(),
                    "annee": date_dep.year,
                    "compte": compte,
                    "poste": poste,
                    "fournisseur": fournisseur,
                    "montant_ttc": montant
                }).eq("id", id_sel).execute()

                st.success("Dépense modifiée.")
                st.rerun()

    # =========================
    # 8. SUPPRIMER
    # =========================
    with tab_delete:
        st.subheader("Supprimer une dépense")

        if df_annee.empty:
            st.info("Aucune dépense à supprimer.")
        else:
            id_del = st.selectbox("Sélectionner", df_annee["id"])
            if st.button("🗑 Supprimer définitivement"):
                supabase.table("depenses").delete().eq("id", id_del).execute()
                st.success("Dépense supprimée.")
                st.rerun()