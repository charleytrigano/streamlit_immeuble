import streamlit as st
import pandas as pd
from datetime import date


def euro(x):
    if x is None:
        return "0,00 €"
    return f"{x:,.2f} €".replace(",", " ").replace(".", ",")


def depenses_ui(supabase, annee):
    st.header(f"📄 Dépenses – {annee}")

    # ======================================================
    # CHARGEMENT DÉPENSES
    # ======================================================
    dep_resp = (
        supabase
        .table("depenses")
        .select("""
            depense_id,
            annee,
            date,
            compte,
            poste,
            fournisseur,
            montant_ttc,
            lot_id,
            commentaire
        """)
        .eq("annee", annee)
        .execute()
    )

    if not dep_resp.data:
        st.warning("Aucune dépense pour cette année.")
        return

    df_dep = pd.DataFrame(dep_resp.data)

    # ======================================================
    # PLAN COMPTABLE (pour groupe_charges)
    # ======================================================
    plan_resp = (
        supabase
        .table("plan_comptable")
        .select("compte_8, groupe_charges, libelle")
        .execute()
    )

    df_plan = pd.DataFrame(plan_resp.data)

    # ======================================================
    # ENRICHISSEMENT
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

    c1, c2, c3 = st.columns(3)

    with c1:
        groupes = ["Tous"] + sorted(df["groupe_charges"].dropna().unique().tolist())
        groupe_sel = st.selectbox("Groupe de charges", groupes)

    with c2:
        comptes = ["Tous"] + sorted(df["compte"].dropna().unique().tolist())
        compte_sel = st.selectbox("Compte", comptes)

    with c3:
        fournisseurs = ["Tous"] + sorted(df["fournisseur"].dropna().unique().tolist())
        fournisseur_sel = st.selectbox("Fournisseur", fournisseurs)

    df_f = df.copy()

    if groupe_sel != "Tous":
        df_f = df_f[df_f["groupe_charges"] == groupe_sel]

    if compte_sel != "Tous":
        df_f = df_f[df_f["compte"] == compte_sel]

    if fournisseur_sel != "Tous":
        df_f = df_f[df_f["fournisseur"] == fournisseur_sel]

    # ======================================================
    # KPI
    # ======================================================
    st.subheader("📊 Indicateurs")

    total = df_f["montant_ttc"].sum()
    nb = len(df_f)
    moy = total / nb if nb else 0

    k1, k2, k3 = st.columns(3)
    k1.metric("Total dépenses", euro(total))
    k2.metric("Nombre de lignes", nb)
    k3.metric("Dépense moyenne", euro(moy))

    # ======================================================
    # ONGLET DÉTAIL / AJOUT
    # ======================================================
    tab_detail, tab_add = st.tabs(["📋 Détail", "➕ Ajouter"])

    # ------------------ DÉTAIL / MODIFIER / SUPPRIMER
    with tab_detail:
        df_view = df_f[[
            "depense_id",
            "date",
            "compte",
            "poste",
            "fournisseur",
            "montant_ttc",
            "lot_id",
            "commentaire",
            "groupe_charges",
            "libelle"
        ]].sort_values("date")

        edited = st.data_editor(
            df_view,
            use_container_width=True,
            num_rows="fixed"
        )

        if st.button("💾 Enregistrer les modifications"):
            for _, r in edited.iterrows():
                supabase.table("depenses").update({
                    "date": r["date"],
                    "compte": r["compte"],
                    "poste": r["poste"],
                    "fournisseur": r["fournisseur"],
                    "montant_ttc": r["montant_ttc"],
                    "lot_id": r["lot_id"],
                    "commentaire": r["commentaire"],
                }).eq("depense_id", r["depense_id"]).execute()

            st.success("Modifications enregistrées")
            st.rerun()

        st.divider()

        dep_del = st.selectbox(
            "Supprimer une dépense",
            df_view["depense_id"]
        )

        if st.button("❌ Supprimer"):
            supabase.table("depenses").delete().eq(
                "depense_id", dep_del
            ).execute()
            st.success("Dépense supprimée")
            st.rerun()

    # ------------------ AJOUT
    with tab_add:
        with st.form("add_depense"):
            d_date = st.date_input("Date", value=date.today())
            d_compte = st.text_input("Compte")
            d_poste = st.text_input("Poste")
            d_fournisseur = st.text_input("Fournisseur")
            d_montant = st.number_input("Montant TTC", min_value=0.0)
            d_lot = st.number_input("Lot ID", min_value=0)
            d_commentaire = st.text_area("Commentaire")

            if st.form_submit_button("Ajouter"):
                supabase.table("depenses").insert({
                    "annee": annee,
                    "date": d_date,
                    "compte": d_compte,
                    "poste": d_poste,
                    "fournisseur": d_fournisseur,
                    "montant_ttc": d_montant,
                    "lot_id": d_lot,
                    "commentaire": d_commentaire,
                }).execute()

                st.success("Dépense ajoutée")
                st.rerun()

    # ======================================================
    # RÉCAP PAR GROUPE DE CHARGES
    # ======================================================
    st.subheader("📊 Dépenses par groupe de charges")

    recap = (
        df_f
        .groupby("groupe_charges", as_index=False)
        .agg(
            total=("montant_ttc", "sum"),
            nb=("montant_ttc", "count")
        )
    )

    st.dataframe(recap, use_container_width=True)