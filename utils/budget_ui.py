import streamlit as st
import pandas as pd
from datetime import datetime


def budget_ui(supabase):
    st.header("💰 Budget annuel")

    # =========================
    # 1. CHARGEMENT DES DONNÉES
    # =========================
    resp = supabase.table("budgets").select("*").execute()
    data = resp.data if resp.data else []
    df = pd.DataFrame(data)

    if not df.empty:
        df["annee"] = df["annee"].astype(int)
        df["compte"] = df["compte"].astype(str)
        df["budget"] = df["budget"].astype(float)

    # =========================
    # 2. ANNÉE BUDGÉTAIRE (LIBRE)
    # =========================
    current_year = datetime.now().year

    annee_selectionnee = st.number_input(
        "Année budgétaire",
        min_value=2000,
        max_value=current_year + 10,
        value=current_year,
        step=1
    )

    df_annee = df[df["annee"] == annee_selectionnee] if not df.empty else pd.DataFrame()

    # =========================
    # 3. KPI
    # =========================
    if not df_annee.empty:
        total_budget = df_annee["budget"].sum()
        nb_comptes = df_annee["compte"].nunique()
        budget_moyen = total_budget / nb_comptes if nb_comptes else 0
    else:
        total_budget = 0
        nb_comptes = 0
        budget_moyen = 0

    col1, col2, col3 = st.columns(3)
    col1.metric("Budget total (€)", f"{total_budget:,.2f}")
    col2.metric("Nombre de comptes", nb_comptes)
    col3.metric("Budget moyen (€)", f"{budget_moyen:,.2f}")

    # =========================
    # 4. ONGLETS
    # =========================
    tab_consult, tab_add, tab_edit, tab_delete = st.tabs(
        ["📊 Consulter", "➕ Ajouter", "✏️ Modifier", "🗑️ Supprimer"]
    )

    # =========================
    # 5. CONSULTER
    # =========================
    with tab_consult:
        if df_annee.empty:
            st.info("Aucun budget pour cette année.")
        else:
            st.dataframe(
                df_annee.sort_values("compte"),
                use_container_width=True
            )

    # =========================
    # 6. AJOUTER
    # =========================
    with tab_add:
        st.subheader("Ajouter un budget")

        with st.form("add_budget_form"):
            compte = st.text_input("Compte", placeholder="ex : 601")
            budget = st.number_input("Budget (€)", min_value=0.0, step=50.0)
            groupe = st.text_input("Groupe de compte (optionnel)")

            submit = st.form_submit_button("💾 Enregistrer")

        if submit:
            if not compte:
                st.error("Le compte est obligatoire.")
            else:
                payload = {
                    "annee": int(annee_selectionnee),
                    "compte": compte,
                    "budget": float(budget),
                    "groupe_compte": groupe or compte,
                }

                try:
                    supabase.table("budgets").insert(payload).execute()
                    st.success("Budget ajouté avec succès.")
                    st.rerun()
                except Exception as e:
                    st.error("Erreur lors de l'ajout du budget.")
                    st.exception(e)

    # =========================
    # 7. MODIFIER
    # =========================
    with tab_edit:
        st.subheader("Modifier un budget")

        if df_annee.empty:
            st.info("Aucun budget à modifier pour cette année.")
        else:
            ids = df_annee["id"].tolist()
            id_sel = st.selectbox("Sélectionner un budget", ids)

            row = df_annee[df_annee["id"] == id_sel].iloc[0]

            with st.form("edit_budget_form"):
                compte = st.text_input("Compte", value=row["compte"])
                budget = st.number_input("Budget (€)", value=float(row["budget"]), step=50.0)
                groupe = st.text_input("Groupe de compte", value=row["groupe_compte"])

                submit_edit = st.form_submit_button("✏️ Mettre à jour")

            if submit_edit:
                try:
                    supabase.table("budgets").update({
                        "compte": compte,
                        "budget": budget,
                        "groupe_compte": groupe
                    }).eq("id", id_sel).execute()

                    st.success("Budget modifié.")
                    st.rerun()
                except Exception as e:
                    st.error("Erreur lors de la modification.")
                    st.exception(e)

    # =========================
    # 8. SUPPRIMER
    # =========================
    with tab_delete:
        st.subheader("Supprimer un budget")

        if df_annee.empty:
            st.info("Aucun budget à supprimer pour cette année.")
        else:
            id_del = st.selectbox("Sélectionner un budget à supprimer", df_annee["id"])

            if st.button("🗑️ Supprimer définitivement"):
                try:
                    supabase.table("budgets").delete().eq("id", id_del).execute()
                    st.success("Budget supprimé.")
                    st.rerun()
                except Exception as e:
                    st.error("Erreur lors de la suppression.")
                    st.exception(e)