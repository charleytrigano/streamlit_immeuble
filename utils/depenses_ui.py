import streamlit as st
import pandas as pd
from datetime import date


def depenses_ui(supabase):
    st.title("📋 État des dépenses")

    # =========================
    # CHARGEMENT DES DONNÉES
    # =========================
    rows = (
        supabase
        .table("depenses")
        .select("*")
        .order("date", desc=True)
        .execute()
        .data
    )

    if not rows:
        st.info("Aucune dépense enregistrée.")
        return

    df = pd.DataFrame(rows)

    # =========================
    # NORMALISATION (CRITIQUE)
    # =========================
    df["annee"] = df["annee"].astype(int)
    df["compte"] = df["compte"].fillna("").astype(str)
    df["poste"] = df["poste"].fillna("—").astype(str)
    df["fournisseur"] = df["fournisseur"].fillna("—").astype(str)
    df["type"] = df["type"].fillna("Charge").astype(str)
    df["montant_ttc"] = df["montant_ttc"].astype(float)

    # =========================
    # FILTRES
    # =========================
    st.subheader("Filtres")

    col1, col2, col3, col4, col5 = st.columns(5)

    with col1:
        annees = sorted(df["annee"].unique())
        annee = st.selectbox("Année", annees, index=len(annees) - 1)

    df_f = df[df["annee"] == annee].copy()

    with col2:
        comptes = sorted(df_f["compte"].unique())
        sel_comptes = st.multiselect("Compte", comptes, default=comptes)

    with col3:
        fournisseurs = sorted(df_f["fournisseur"].unique())
        sel_fournisseurs = st.multiselect("Fournisseur", fournisseurs, default=fournisseurs)

    with col4:
        postes = sorted(df_f["poste"].unique())
        sel_postes = st.multiselect("Poste", postes, default=postes)

    with col5:
        types = ["Charge", "Avoir", "Remboursement"]
        sel_types = st.multiselect("Type", types, default=types)

    # =========================
    # APPLICATION DES FILTRES
    # =========================
    df_f = df_f[
        df_f["compte"].isin(sel_comptes)
        & df_f["fournisseur"].isin(sel_fournisseurs)
        & df_f["poste"].isin(sel_postes)
        & df_f["type"].isin(sel_types)
    ]

    # =========================
    # KPI (APRÈS FILTRES)
    # =========================
    total = df_f["montant_ttc"].sum()
    nb = len(df_f)
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
        st.dataframe(
            df_f.sort_values("date", ascending=False),
            use_container_width=True
        )

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

            submit = st.form_submit_button("💾 Enregistrer")

        if submit:
            montant_final = (
                -abs(montant)
                if type_depense in ["Avoir", "Remboursement"]
                else abs(montant)
            )

            supabase.table("depenses").insert({
                "annee": d.year,
                "date": d.isoformat(),
                "compte": compte,
                "poste": poste,
                "fournisseur": fournisseur,
                "montant_ttc": montant_final,
                "type": type_depense,
            }).execute()

            st.success("Dépense enregistrée")
            st.rerun()

    # =========================
    # MODIFIER
    # =========================
    with tab_modifier:
        if df_f.empty:
            st.info("Aucune dépense à modifier.")
        else:
            dep_id = st.selectbox(
                "Sélectionner une dépense",
                df_f["id"],
                key="edit_dep"
            )

            dep = df[df["id"] == dep_id].iloc[0]

            with st.form("edit_depense"):
                new_date = st.date_input("Date", value=pd.to_datetime(dep["date"]))
                new_compte = st.text_input("Compte", dep["compte"])
                new_poste = st.text_input("Poste", dep["poste"])
                new_fournisseur = st.text_input("Fournisseur", dep["fournisseur"])

                new_montant = st.number_input(
                    "Montant TTC (€)",
                    value=abs(dep["montant_ttc"]),
                    step=0.01,
                    format="%.2f"
                )

                new_type = st.selectbox(
                    "Type",
                    ["Charge", "Avoir", "Remboursement"],
                    index=["Charge", "Avoir", "Remboursement"].index(dep["type"])
                )

                save = st.form_submit_button("💾 Mettre à jour")

            if save:
                montant_final = (
                    -abs(new_montant)
                    if new_type in ["Avoir", "Remboursement"]
                    else abs(new_montant)
                )

                supabase.table("depenses").update({
                    "date": new_date.isoformat(),
                    "annee": new_date.year,
                    "compte": new_compte,
                    "poste": new_poste,
                    "fournisseur": new_fournisseur,
                    "montant_ttc": montant_final,
                    "type": new_type,
                }).eq("id", dep_id).execute()

                st.success("Dépense modifiée")
                st.rerun()

    # =========================
    # SUPPRIMER
    # =========================
    with tab_supprimer:
        if df_f.empty:
            st.info("Aucune dépense à supprimer.")
        else:
            del_id = st.selectbox(
                "Sélectionner une dépense",
                df_f["id"],
                key="delete_dep"
            )

            if st.button("🗑 Supprimer définitivement"):
                supabase.table("depenses").delete().eq("id", del_id).execute()
                st.success("Dépense supprimée")
                st.rerun()