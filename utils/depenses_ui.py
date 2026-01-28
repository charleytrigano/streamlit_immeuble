import streamlit as st
import pandas as pd
from datetime import date


def euro(x):
    return f"{x:,.2f} €".replace(",", " ").replace(".", ",")


def depenses_ui(supabase, annee):
    st.header("📄 État des dépenses")

    # ======================================================
    # CHARGEMENT DES DONNÉES
    # ======================================================
    dep_resp = (
        supabase
        .table("depenses")
        .select("*")
        .eq("annee", annee)
        .execute()
    )
    df_dep = pd.DataFrame(dep_resp.data)

    bud_resp = (
        supabase
        .table("budgets")
        .select("*")
        .eq("annee", annee)
        .execute()
    )
    df_bud = pd.DataFrame(bud_resp.data)

    plan_resp = (
        supabase
        .table("plan_comptable")
        .select("*")
        .execute()
    )
    df_plan = pd.DataFrame(plan_resp.data)

    if df_dep.empty:
        st.warning("Aucune dépense pour cette année.")
        return

    # ======================================================
    # NORMALISATION
    # ======================================================
    df_dep["montant_ttc"] = pd.to_numeric(df_dep["montant_ttc"], errors="coerce").fillna(0)

    # Jointure plan comptable
    if not df_plan.empty:
        df_dep = df_dep.merge(
            df_plan[["compte_8", "groupe_compte", "libelle_groupe"]],
            left_on="compte",
            right_on="compte_8",
            how="left"
        )

    # ======================================================
    # FILTRES
    # ======================================================
    st.sidebar.subheader("🔎 Filtres dépenses")

    comptes = sorted(df_dep["compte"].dropna().unique().tolist())
    fournisseurs = sorted(df_dep["fournisseur"].dropna().unique().tolist())
    postes = sorted(df_dep["poste"].dropna().unique().tolist())
    groupes = sorted(df_dep["groupe_compte"].dropna().unique().tolist())

    f_compte = st.sidebar.selectbox("Compte", ["Tous"] + comptes)
    f_fournisseur = st.sidebar.selectbox("Fournisseur", ["Tous"] + fournisseurs)
    f_poste = st.sidebar.selectbox("Poste", ["Tous"] + postes)
    f_groupe = st.sidebar.selectbox("Groupe de compte", ["Tous"] + groupes)

    df_f = df_dep.copy()

    if f_compte != "Tous":
        df_f = df_f[df_f["compte"] == f_compte]
    if f_fournisseur != "Tous":
        df_f = df_f[df_f["fournisseur"] == f_fournisseur]
    if f_poste != "Tous":
        df_f = df_f[df_f["poste"] == f_poste]
    if f_groupe != "Tous":
        df_f = df_f[df_f["groupe_compte"] == f_groupe]

    # ======================================================
    # KPI
    # ======================================================
    total_dep = df_f["montant_ttc"].sum()

    budget_total = (
        df_bud["budget"].sum()
        if not df_bud.empty and "budget" in df_bud.columns
        else 0
    )

    ecart = total_dep - budget_total
    ecart_pct = (ecart / budget_total * 100) if budget_total != 0 else 0

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("💸 Dépenses", euro(total_dep))
    c2.metric("💰 Budget", euro(budget_total))
    c3.metric("📉 Écart", euro(ecart))
    c4.metric("📊 Écart %", f"{ecart_pct:.2f} %")

    # ======================================================
    # TABLEAU PRINCIPAL
    # ======================================================
    st.subheader("📋 Liste des dépenses")

    df_display = df_f[[
        "date",
        "compte",
        "poste",
        "groupe_compte",
        "libelle_groupe",
        "fournisseur",
        "montant_ttc",
        "type",
        "commentaire",
        "facture_url"
    ]].sort_values("date")

    st.dataframe(df_display, use_container_width=True)

    # ======================================================
    # AJOUT DÉPENSE
    # ======================================================
    st.divider()
    st.subheader("➕ Ajouter une dépense")

    with st.form("add_depense"):
        col1, col2 = st.columns(2)

        with col1:
            d_date = st.date_input("Date", value=date.today())
            d_compte = st.selectbox("Compte", comptes)
            d_poste = st.text_input("Poste")
            d_fournisseur = st.text_input("Fournisseur")

        with col2:
            d_montant = st.number_input("Montant TTC", min_value=0.0, step=0.01)
            d_type = st.selectbox("Type", ["Charge", "Avoir", "Remboursement"])
            d_commentaire = st.text_area("Commentaire")

        submitted = st.form_submit_button("Enregistrer")

        if submitted:
            supabase.table("depenses").insert({
                "annee": annee,
                "date": str(d_date),
                "compte": d_compte,
                "poste": d_poste,
                "fournisseur": d_fournisseur,
                "montant_ttc": d_montant,
                "type": d_type,
                "commentaire": d_commentaire
            }).execute()

            st.success("Dépense ajoutée")
            st.experimental_rerun()

    # ======================================================
    # SUPPRESSION
    # ======================================================
    st.divider()
    st.subheader("🗑️ Supprimer une dépense")

    dep_ids = df_dep["depense_id"].astype(str).tolist()

    dep_to_delete = st.selectbox(
        "Sélectionner une dépense (ID)",
        dep_ids
    )

    if st.button("Supprimer définitivement"):
        supabase.table("depenses").delete().eq(
            "depense_id", dep_to_delete
        ).execute()

        st.success("Dépense supprimée")
        st.experimental_rerun()