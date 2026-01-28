import streamlit as st
import pandas as pd
from datetime import date


# ======================================================
# FORMAT € FR
# ======================================================
def euro(x):
    if x is None:
        return "0,00 €"
    return f"{float(x):,.2f} €".replace(",", " ").replace(".", ",")


# ======================================================
# UI DEPENSES
# ======================================================
def depenses_ui(supabase, annee):
    st.header("📄 État des dépenses")

    # ======================================================
    # CHARGEMENT DES DONNÉES
    # ======================================================
    dep = supabase.table("depenses").select("*").eq("annee", annee).execute().data
    bud = supabase.table("budgets").select("*").eq("annee", annee).execute().data
    plan = supabase.table("plan_comptable").select("*").execute().data

    df_dep = pd.DataFrame(dep)
    df_bud = pd.DataFrame(bud)
    df_plan = pd.DataFrame(plan)

    if df_dep.empty:
        st.warning("Aucune dépense pour cette année")
        return

    # ======================================================
    # ENRICHISSEMENT DEPENSES AVEC PLAN COMPTABLE
    # ======================================================
    df_dep = df_dep.merge(
        df_plan,
        left_on="compte",
        right_on="compte_8",
        how="left"
    )

    # ======================================================
    # SIDEBAR — FILTRES
    # ======================================================
    st.sidebar.subheader("Filtres dépenses")

    comptes = sorted(df_dep["compte"].dropna().unique())
    fournisseurs = sorted(df_dep["fournisseur"].dropna().unique())
    postes = sorted(df_dep["poste"].dropna().unique())
    groupes = sorted(df_dep["groupe_compte"].dropna().unique())

    f_compte = st.sidebar.multiselect("Compte", comptes)
    f_fournisseur = st.sidebar.multiselect("Fournisseur", fournisseurs)
    f_poste = st.sidebar.multiselect("Poste", postes)
    f_groupe = st.sidebar.multiselect("Groupe de compte", groupes)

    df_f = df_dep.copy()

    if f_compte:
        df_f = df_f[df_f["compte"].isin(f_compte)]
    if f_fournisseur:
        df_f = df_f[df_f["fournisseur"].isin(f_fournisseur)]
    if f_poste:
        df_f = df_f[df_f["poste"].isin(f_poste)]
    if f_groupe:
        df_f = df_f[df_f["groupe_compte"].isin(f_groupe)]

    # ======================================================
    # KPI
    # ======================================================
    total_dep = df_f["montant_ttc"].sum()

    budget_total = (
        df_bud["budget"].sum()
        if not df_bud.empty
        else 0
    )

    ecart = total_dep - budget_total
    pct = (total_dep / budget_total * 100) if budget_total > 0 else 0

    c1, c2, c3, c4 = st.columns(4)

    c1.metric("Total dépenses", euro(total_dep))
    c2.metric("Budget", euro(budget_total))
    c3.metric("Écart", euro(ecart))
    c4.metric("% budget", f"{pct:.1f} %")

    # ======================================================
    # TABLEAU DEPENSES
    # ======================================================
    st.subheader("📋 Liste des dépenses")

    df_display = df_f[[
        "date",
        "compte",
        "libelle",
        "poste",
        "fournisseur",
        "montant_ttc",
        "type",
        "commentaire"
    ]].sort_values("date")

    st.dataframe(df_display, use_container_width=True)

    # ======================================================
    # AJOUT / MODIFICATION
    # ======================================================
    st.subheader("➕ Ajouter / ✏️ Modifier une dépense")

    with st.form("form_depense"):
        dep_id = st.selectbox(
            "Dépense à modifier (laisser vide pour création)",
            options=[""] + df_dep["depense_id"].astype(str).tolist()
        )

        compte = st.selectbox("Compte", comptes)
        poste = st.text_input("Poste")
        fournisseur = st.text_input("Fournisseur")
        date_dep = st.date_input("Date", value=date.today())
        montant = st.number_input("Montant TTC", step=0.01)
        type_dep = st.selectbox("Type", ["Charge", "Avoir", "Remboursement"])
        commentaire = st.text_area("Commentaire")

        submit = st.form_submit_button("Enregistrer")

        if submit:
            payload = {
                "annee": annee,
                "compte": compte,
                "poste": poste,
                "fournisseur": fournisseur,
                "date": date_dep.isoformat(),
                "montant_ttc": montant,
                "type": type_dep,
                "commentaire": commentaire
            }

            if dep_id:
                supabase.table("depenses").update(payload).eq("depense_id", dep_id).execute()
                st.success("Dépense modifiée")
            else:
                supabase.table("depenses").insert(payload).execute()
                st.success("Dépense ajoutée")

            st.experimental_rerun()

    # ======================================================
    # SUPPRESSION
    # ======================================================
    st.subheader("🗑️ Supprimer une dépense")

    del_id = st.selectbox(
        "Sélectionner une dépense",
        df_dep["depense_id"].astype(str)
    )

    if st.button("Supprimer définitivement"):
        supabase.table("depenses").delete().eq("depense_id", del_id).execute()
        st.success("Dépense supprimée")
        st.experimental_rerun()