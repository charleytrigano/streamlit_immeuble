import streamlit as st
import pandas as pd
from datetime import date


def euro(x):
    return f"{x:,.2f} €".replace(",", " ").replace(".", ",")


def depenses_ui(supabase, annee):
    st.header("📄 Dépenses")

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

    plan_resp = (
        supabase
        .table("plan_comptable")
        .select("compte_8, libelle, groupe_charges")
        .execute()
    )

    if not dep_resp.data:
        st.warning("Aucune dépense pour cette année.")
        return

    df_dep = pd.DataFrame(dep_resp.data)
    df_plan = pd.DataFrame(plan_resp.data)

    # ======================================================
    # ENRICHISSEMENT (jointure maîtrisée)
    # ======================================================
    df = df_dep.merge(
        df_plan,
        left_on="compte",
        right_on="compte_8",
        how="left"
    )

    # ======================================================
    # FILTRES
    # ======================================================
    st.subheader("🔎 Filtres")

    col1, col2, col3 = st.columns(3)

    with col1:
        groupes = ["Tous"] + sorted(df["groupe_charges"].dropna().unique().tolist())
        groupe_sel = st.selectbox("Groupe de charges", groupes)

    with col2:
        comptes = ["Tous"] + sorted(df["compte"].dropna().unique().tolist())
        compte_sel = st.selectbox("Compte", comptes)

    with col3:
        fournisseurs = ["Tous"] + sorted(df["fournisseur"].dropna().unique().tolist())
        fournisseur_sel = st.selectbox("Fournisseur", fournisseurs)

    if groupe_sel != "Tous":
        df = df[df["groupe_charges"] == groupe_sel]

    if compte_sel != "Tous":
        df = df[df["compte"] == compte_sel]

    if fournisseur_sel != "Tous":
        df = df[df["fournisseur"] == fournisseur_sel]

    # ======================================================
    # KPI
    # ======================================================
    st.subheader("📊 Indicateurs")

    total = df["montant_ttc"].sum()
    nb = len(df)
    moyenne = total / nb if nb > 0 else 0

    k1, k2, k3 = st.columns(3)
    k1.metric("Total dépenses", euro(total))
    k2.metric("Nombre d'écritures", nb)
    k3.metric("Montant moyen", euro(moyenne))

    # ======================================================
    # TABLEAU DÉTAIL (lecture)
    # ======================================================
    st.subheader("📋 Détail des dépenses")

    cols_affichees = [
        "date",
        "compte",
        "libelle",
        "poste",
        "fournisseur",
        "montant_ttc",
        "groupe_charges",
        "commentaire",
    ]

    st.dataframe(
        df[cols_affichees].sort_values("date"),
        use_container_width=True
    )

    # ======================================================
    # AJOUT DÉPENSE
    # ======================================================
    st.subheader("➕ Ajouter une dépense")

    with st.form("add_depense"):
        c1, c2, c3 = st.columns(3)

        with c1:
            d_date = st.date_input("Date", value=date.today())
            d_compte = st.selectbox("Compte", sorted(df_plan["compte_8"].unique()))

        with c2:
            d_poste = st.text_input("Poste")
            d_fournisseur = st.text_input("Fournisseur")

        with c3:
            d_montant = st.number_input("Montant TTC", min_value=0.0, step=10.0)

        d_commentaire = st.text_area("Commentaire")

        submitted = st.form_submit_button("💾 Ajouter")

        if submitted:
            supabase.table("depenses").insert({
                "annee": annee,
                "date": d_date.isoformat(),
                "compte": d_compte,
                "poste": d_poste,
                "fournisseur": d_fournisseur,
                "montant_ttc": d_montant,
                "commentaire": d_commentaire,
            }).execute()

            st.success("Dépense ajoutée")
            st.rerun()

    # ======================================================
    # MODIFICATION / SUPPRESSION
    # ======================================================
    st.subheader("✏️ Modifier / 🗑 Supprimer")

    depense_ids = df["depense_id"].tolist() if "depense_id" in df.columns else df["id"].tolist()
    id_sel = st.selectbox("Sélectionner une dépense", depense_ids)

    dep = df[df["depense_id"] == id_sel].iloc[0]

    with st.form("edit_depense"):
        e1, e2, e3 = st.columns(3)

        with e1:
            e_date = st.date_input("Date", pd.to_datetime(dep["date"]))
            e_compte = st.selectbox(
                "Compte",
                sorted(df_plan["compte_8"].unique()),
                index=list(df_plan["compte_8"]).index(dep["compte"])
            )

        with e2:
            e_poste = st.text_input("Poste", dep["poste"])
            e_fournisseur = st.text_input("Fournisseur", dep["fournisseur"])

        with e3:
            e_montant = st.number_input("Montant TTC", value=float(dep["montant_ttc"]), step=10.0)

        e_commentaire = st.text_area("Commentaire", dep["commentaire"])

        col_save, col_del = st.columns(2)

        if col_save.form_submit_button("💾 Enregistrer"):
            supabase.table("depenses").update({
                "date": e_date.isoformat(),
                "compte": e_compte,
                "poste": e_poste,
                "fournisseur": e_fournisseur,
                "montant_ttc": e_montant,
                "commentaire": e_commentaire,
            }).eq("id", id_sel).execute()

            st.success("Dépense mise à jour")
            st.rerun()

        if col_del.form_submit_button("🗑 Supprimer"):
            supabase.table("depenses").delete().eq("id", id_sel).execute()
            st.warning("Dépense supprimée")
            st.rerun()