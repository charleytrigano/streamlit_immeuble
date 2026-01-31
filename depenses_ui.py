import streamlit as st
import pandas as pd
from datetime import date


def depenses_ui(supabase, annee):
    st.header(f"📄 Dépenses – {annee}")

    tab_edit, tab_group = st.tabs([
        "✏️ Détail / Ajouter / Modifier / Supprimer",
        "📊 Dépenses par groupes de charges"
    ])

    # ======================================================
    # ONGLET 1 — CRUD DÉPENSES (TABLE depenses)
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

        # ---------- Filtres ----------
        st.subheader("🔎 Filtres")

        colf1, colf2 = st.columns(2)

        with colf1:
            fournisseurs = ["Tous"] + sorted(df["fournisseur"].dropna().unique().tolist()) if not df.empty else ["Tous"]
            fournisseur_sel = st.selectbox("Fournisseur", fournisseurs)

        with colf2:
            comptes = ["Tous"] + sorted(df["compte"].dropna().unique().tolist()) if not df.empty else ["Tous"]
            compte_sel = st.selectbox("Compte", comptes)

        df_f = df.copy()
        if fournisseur_sel != "Tous":
            df_f = df_f[df_f["fournisseur"] == fournisseur_sel]
        if compte_sel != "Tous":
            df_f = df_f[df_f["compte"] == compte_sel]

        # ---------- Tableau éditable ----------
        st.subheader("✏️ Édition des dépenses")

        edited_df = st.data_editor(
            df_f,
            use_container_width=True,
            num_rows="dynamic",
            key="depenses_editor"
        )

        # ---------- Sauvegarde ----------
        if st.button("💾 Enregistrer les modifications"):
            for _, row in edited_df.iterrows():
                if pd.isna(row.get("depense_id")):
                    # ➕ AJOUT
                    supabase.table("depenses").insert({
                        "annee": annee,
                        "date": row["date"],
                        "compte": row["compte"],
                        "poste": row["poste"],
                        "fournisseur": row["fournisseur"],
                        "montant_ttc": row["montant_ttc"],
                        "lot_id": row["lot_id"],
                        "commentaire": row["commentaire"],
                    }).execute()
                else:
                    # ✏️ MODIFICATION
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
        st.subheader("🗑 Supprimer une dépense")

        if not df.empty:
            dep_to_delete = st.selectbox(
                "Sélectionne une dépense",
                df["depense_id"]
            )

            if st.button("❌ Supprimer définitivement"):
                supabase.table("depenses").delete().eq(
                    "depense_id", dep_to_delete
                ).execute()
                st.success("Dépense supprimée")
                st.rerun()

    # ======================================================
    # ONGLET 2 — DÉPENSES PAR GROUPES (LECTURE SEULE)
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