import streamlit as st
import pandas as pd
from datetime import date


def depenses_ui(supabase, annee):
    st.header(f"📄 Dépenses – {annee}")

    tab_add, tab_edit, tab_group = st.tabs([
        "➕ Ajouter une dépense",
        "✏️ Modifier / Supprimer",
        "📊 Dépenses par groupes de charges"
    ])

    # ======================================================
    # ONGLET 1 — AJOUT
    # ======================================================
    with tab_add:
        st.subheader("➕ Nouvelle dépense")

        with st.form("add_depense"):
            col1, col2 = st.columns(2)

            with col1:
                d_date = st.date_input("Date", value=date.today())
                d_compte = st.text_input("Compte")
                d_poste = st.text_input("Poste")
                d_fournisseur = st.text_input("Fournisseur")

            with col2:
                d_montant = st.number_input("Montant TTC", min_value=0.0, step=10.0)
                d_lot = st.number_input("Lot ID", min_value=0, step=1)
                d_commentaire = st.text_area("Commentaire")

            submitted = st.form_submit_button("💾 Ajouter la dépense")

            if submitted:
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
    # ONGLET 2 — MODIFIER / SUPPRIMER
    # ======================================================
    with tab_edit:
        resp = (
            supabase
            .table("depenses")
            .select("""
                depense_id,
                date,
                compte,
                poste,
                fournisseur,
                montant_ttc,
                lot_id,
                commentaire
            """)
            .eq("annee", annee)
            .order("date")
            .execute()
        )

        df = pd.DataFrame(resp.data) if resp.data else pd.DataFrame()

        if df.empty:
            st.info("Aucune dépense")
            return

        # ---------- Filtres ----------
        colf1, colf2 = st.columns(2)

        with colf1:
            fournisseurs = ["Tous"] + sorted(df["fournisseur"].dropna().unique())
            fournisseur_sel = st.selectbox("Fournisseur", fournisseurs)

        with colf2:
            comptes = ["Tous"] + sorted(df["compte"].dropna().unique())
            compte_sel = st.selectbox("Compte", comptes)

        df_f = df.copy()
        if fournisseur_sel != "Tous":
            df_f = df_f[df_f["fournisseur"] == fournisseur_sel]
        if compte_sel != "Tous":
            df_f = df_f[df_f["compte"] == compte_sel]

        # ---------- Edition ----------
        edited_df = st.data_editor(
            df_f,
            use_container_width=True,
            num_rows="fixed",
            key="depenses_edit"
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

        # ---------- Suppression ----------
        st.subheader("🗑 Supprimer")

        dep_to_delete = st.selectbox(
            "Dépense à supprimer",
            df["depense_id"]
        )

        if st.button("❌ Supprimer définitivement"):
            supabase.table("depenses").delete().eq(
                "depense_id", dep_to_delete
            ).execute()
            st.success("Dépense supprimée")
            st.rerun()

    # ======================================================
    # ONGLET 3 — PAR GROUPES DE CHARGES (LECTURE SEULE)
    # ======================================================
    with tab_group:
        resp = (
            supabase
            .table("v_depenses_enrichies")
            .select("groupe_charges, montant_ttc")
            .eq("annee", annee)
            .execute()
        )

        if not resp.data:
            st.info("Aucune donnée")
            return

        df = pd.DataFrame(resp.data)

        df_group = (
            df
            .groupby("groupe_charges", as_index=False)
            .agg(
                total=("montant_ttc", "sum"),
                nb=("montant_ttc", "count")
            )
            .sort_values("groupe_charges")
        )

        col1, col2 = st.columns(2)
        col1.metric("Total dépenses", f"{df_group['total'].sum():,.2f} €".replace(",", " "))
        col2.metric("Nombre de lignes", int(df_group["nb"].sum()))

        st.dataframe(
            df_group.rename(columns={
                "groupe_charges": "Groupe de charges",
                "total": "Total (€)",
                "nb": "Nombre de dépenses"
            }),
            use_container_width=True
        )