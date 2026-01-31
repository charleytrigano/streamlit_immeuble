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
    # CHARGEMENT DONNÉES ENRICHIES (BASE UNIQUE)
    # ======================================================
    resp = (
        supabase
        .table("v_depenses_enrichies")
        .select("*")
        .eq("annee", annee)
        .execute()
    )

    if not resp.data:
        st.warning("Aucune dépense pour cette année.")
        return

    df = pd.DataFrame(resp.data)

    # ======================================================
    # FILTRES
    # ======================================================
    st.subheader("🔎 Filtres")

    colf1, colf2, colf3 = st.columns(3)

    with colf1:
        groupes = ["Tous"] + sorted(df["groupe_charges"].dropna().unique().tolist())
        groupe_sel = st.selectbox("Groupe de charges", groupes)

    with colf2:
        comptes = ["Tous"] + sorted(df["compte"].dropna().unique().tolist())
        compte_sel = st.selectbox("Compte", comptes)

    with colf3:
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

    total_dep = df_f["montant_ttc"].sum()
    nb_dep = len(df_f)
    dep_moy = total_dep / nb_dep if nb_dep else 0

    k1, k2, k3 = st.columns(3)
    k1.metric("Total dépenses", euro(total_dep))
    k2.metric("Nombre de lignes", nb_dep)
    k3.metric("Dépense moyenne", euro(dep_moy))

    # ======================================================
    # ONGLET DÉTAIL / AJOUT
    # ======================================================
    tab_detail, tab_add = st.tabs([
        "📋 Détail des dépenses",
        "➕ Ajouter une dépense"
    ])

    # ======================================================
    # DÉTAIL + MODIFICATION / SUPPRESSION
    # ======================================================
    with tab_detail:
        st.subheader("📋 Détail")

        cols = [
            "depense_id",
            "date",
            "compte",
            "poste",
            "fournisseur",
            "montant_ttc",
            "lot_id",
            "commentaire",
            "groupe_charges",
            "libelle_compte",
        ]

        df_view = df_f[cols].sort_values("date")

        edited_df = st.data_editor(
            df_view,
            use_container_width=True,
            num_rows="fixed",
            key="depenses_editor"
        )

        if st.button("💾 Enregistrer les modifications"):
            for _, row in edited_df.iterrows():
                supabase.table("depenses").update({
                    "date": row["date"],
                    "compte": row["compte"],
                    "poste": row["poste"],
                    "fournisseur": row["fournisseur"],
                    "montant_ttc": row["montant_ttc"],
                    "lot_id": row["lot_id"],
                    "commentaire": row["commentaire"],
                }).eq("depense_id", row["depense_id"]).execute()

            st.success("✅ Modifications enregistrées")
            st.rerun()

        st.divider()

        st.subheader("🗑 Supprimer une dépense")

        dep_del = st.selectbox(
            "Sélection",
            df_view["depense_id"],
            format_func=lambda x: f"Dépense {x}"
        )

        if st.button("❌ Supprimer définitivement"):
            supabase.table("depenses").delete().eq(
                "depense_id", dep_del
            ).execute()
            st.success("Dépense supprimée")
            st.rerun()

    # ======================================================
    # AJOUT
    # ======================================================
    with tab_add:
        st.subheader("➕ Nouvelle dépense")

        with st.form("add_depense"):
            c1, c2 = st.columns(2)

            with c1:
                d_date = st.date_input("Date", value=date.today())
                d_compte = st.text_input("Compte")
                d_poste = st.text_input("Poste")
                d_fournisseur = st.text_input("Fournisseur")

            with c2:
                d_montant = st.number_input("Montant TTC", min_value=0.0, step=10.0)
                d_lot = st.number_input("Lot ID", min_value=0, step=1)
                d_commentaire = st.text_area("Commentaire")

            submit = st.form_submit_button("💾 Ajouter")

            if submit:
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

                st.success("✅ Dépense ajoutée")
                st.rerun()

    # ======================================================
    # RÉCAP PAR GROUPE DE CHARGES
    # ======================================================
    st.subheader("📊 Dépenses par groupe de charges")

    df_group = (
        df_f
        .groupby("groupe_charges", as_index=False)
        .agg(
            total=("montant_ttc", "sum"),
            nb=("montant_ttc", "count")
        )
        .sort_values("groupe_charges")
    )

    st.dataframe(
        df_group.rename(columns={
            "groupe_charges": "Groupe de charges",
            "total": "Total (€)",
            "nb": "Nombre de dépenses"
        }),
        use_container_width=True
    )