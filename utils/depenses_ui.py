import streamlit as st
import pandas as pd
from datetime import date


def depenses_ui(supabase):
    st.title("📄 État des dépenses")

    # ======================================================
    # CHARGEMENT DES DONNÉES
    # ======================================================
    dep = supabase.table("depenses").select("*").execute()
    bud = supabase.table("budgets").select("*").execute()
    plan = supabase.table("plan_comptable").select("*").execute()

    df_dep = pd.DataFrame(dep.data) if dep.data else pd.DataFrame()
    df_bud = pd.DataFrame(bud.data) if bud.data else pd.DataFrame()
    df_plan = pd.DataFrame(plan.data)

    if df_dep.empty:
        st.warning("Aucune dépense enregistrée.")
        return

    # ======================================================
    # ENRICHISSEMENT
    # ======================================================
    df_dep["date"] = pd.to_datetime(df_dep["date"], errors="coerce")
    df_dep["annee"] = df_dep["date"].dt.year

    df_dep = df_dep.merge(
        df_plan[["compte_8", "groupe_compte", "libelle_groupe"]],
        left_on="compte",
        right_on="compte_8",
        how="left"
    )

    # ======================================================
    # SIDEBAR – FILTRES
    # ======================================================
    st.sidebar.header("🎛️ Filtres")

    annee_sel = st.sidebar.multiselect(
        "Année",
        sorted(df_dep["annee"].dropna().unique()),
        default=sorted(df_dep["annee"].dropna().unique())
    )

    groupe_sel = st.sidebar.multiselect(
        "Groupe de compte",
        sorted(df_dep["groupe_compte"].dropna().astype(str).unique())
    )

    compte_sel = st.sidebar.multiselect(
        "Compte",
        sorted(df_dep["compte"].dropna().unique())
    )

    fournisseur_sel = st.sidebar.multiselect(
        "Fournisseur",
        sorted(df_dep["fournisseur"].dropna().unique())
    )

    poste_sel = st.sidebar.multiselect(
        "Poste",
        sorted(df_dep["poste"].dropna().unique())
    )

    type_sel = st.sidebar.multiselect(
        "Type",
        sorted(df_dep["type"].dropna().unique())
    )

    # ======================================================
    # APPLICATION DES FILTRES
    # ======================================================
    df_f = df_dep.copy()

    if annee_sel:
        df_f = df_f[df_f["annee"].isin(annee_sel)]
    if groupe_sel:
        df_f = df_f[df_f["groupe_compte"].astype(str).isin(groupe_sel)]
    if compte_sel:
        df_f = df_f[df_f["compte"].isin(compte_sel)]
    if fournisseur_sel:
        df_f = df_f[df_f["fournisseur"].isin(fournisseur_sel)]
    if poste_sel:
        df_f = df_f[df_f["poste"].isin(poste_sel)]
    if type_sel:
        df_f = df_f[df_f["type"].isin(type_sel)]

    # ======================================================
    # KPI DÉPENSES
    # ======================================================
    total_dep = df_f["montant_ttc"].sum()
    nb_lignes = len(df_f)

    # ======================================================
    # KPI BUDGET
    # ======================================================
    budget_total = 0.0

    if not df_bud.empty and annee_sel:
        df_bf = df_bud[df_bud["annee"].isin(annee_sel)]

        if compte_sel and "compte" in df_bf.columns:
            df_bf = df_bf[df_bf["compte"].isin(compte_sel)]
        elif groupe_sel:
            df_bf["groupe_compte"] = df_bf["groupe_compte"].astype(str)
            df_bf = df_bf[df_bf["groupe_compte"].isin(groupe_sel)]

        budget_total = df_bf["budget"].sum()

    ecart = budget_total - total_dep
    ecart_pct = (ecart / budget_total * 100) if budget_total else 0

    # ======================================================
    # AFFICHAGE KPI
    # ======================================================
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("💰 Dépenses", f"{total_dep:,.2f} €")
    c2.metric("📊 Budget", f"{budget_total:,.2f} €")
    c3.metric("📉 Écart (€)", f"{ecart:,.2f} €")
    c4.metric("📐 Écart (%)", f"{ecart_pct:,.1f} %")

    # ======================================================
    # TABLEAU
    # ======================================================
    st.dataframe(
        df_f[
            [
                "date",
                "annee",
                "groupe_compte",
                "libelle_groupe",
                "compte",
                "poste",
                "fournisseur",
                "montant_ttc",
                "type",
                "commentaire",
            ]
        ].sort_values("date"),
        use_container_width=True
    )

    # ======================================================
    # AJOUT DÉPENSE
    # ======================================================
    st.divider()
    st.subheader("➕ Ajouter une dépense")

    with st.form("add_depense"):
        d = st.date_input("Date", value=date.today())
        compte = st.selectbox("Compte", sorted(df_plan["compte_8"].unique()))
        poste = st.text_input("Poste")
        fournisseur = st.text_input("Fournisseur")
        montant = st.number_input("Montant TTC", step=0.01)
        type_dep = st.text_input("Type")
        commentaire = st.text_area("Commentaire")

        if st.form_submit_button("Ajouter"):
            supabase.table("depenses").insert({
                "date": d.isoformat(),
                "compte": compte,
                "poste": poste,
                "fournisseur": fournisseur,
                "montant_ttc": montant,
                "type": type_dep,
                "commentaire": commentaire,
            }).execute()
            st.success("Dépense ajoutée")
            st.rerun()

    # ======================================================
    # MODIFIER / SUPPRIMER
    # ======================================================
    st.divider()
    st.subheader("✏️ Modifier / 🗑️ Supprimer")

    dep_id = st.selectbox(
        "Sélectionner une dépense",
        df_dep["depense_id"],
        format_func=lambda x: f"{x}"
    )

    dep_sel = df_dep[df_dep["depense_id"] == dep_id].iloc[0]

    with st.form("edit_depense"):
        montant = st.number_input("Montant TTC", value=float(dep_sel["montant_ttc"]))
        commentaire = st.text_area("Commentaire", value=dep_sel.get("commentaire", ""))

        col1, col2 = st.columns(2)

        if col1.form_submit_button("Modifier"):
            supabase.table("depenses").update({
                "montant_ttc": montant,
                "commentaire": commentaire
            }).eq("depense_id", dep_id).execute()
            st.success("Dépense modifiée")
            st.rerun()

        if col2.form_submit_button("Supprimer"):
            supabase.table("depenses").delete().eq("depense_id", dep_id).execute()
            st.warning("Dépense supprimée")
            st.rerun()