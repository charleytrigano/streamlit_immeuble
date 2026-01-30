import streamlit as st
import pandas as pd


def depenses_ui(supabase, annee):
    st.subheader(f"📄 Dépenses – {annee}")

    # =========================
    # CHARGEMENT ROBUSTE
    # =========================
    try:
        res = (
            supabase
            .table("depenses")
            .select("*")
            .execute()
        )
    except Exception as e:
        st.error("❌ Erreur Supabase lors du chargement des dépenses")
        st.exception(e)
        st.stop()

    if not res.data:
        st.info("Aucune dépense en base")
        return

    df = pd.DataFrame(res.data)

    # =========================
    # FILTRE ANNÉE (CÔTÉ PYTHON)
    # =========================
    if "annee" not in df.columns:
        st.error("❌ Colonne `annee` absente de la table depenses")
        return

    df = df[df["annee"] == annee]

    if df.empty:
        st.info("Aucune dépense pour cette année")
        return

    # =========================
    # COLONNES UTILISÉES
    # =========================
    colonnes = [
        "depense_id",
        "date",
        "compte",
        "poste",
        "fournisseur",
        "montant_ttc",
        "lot_id",
        "commentaire"
    ]

    missing = [c for c in colonnes if c not in df.columns]
    if missing:
        st.error(f"❌ Colonnes manquantes dans depenses : {missing}")
        return

    df = df[colonnes].sort_values("date")

    # =========================
    # TABLE ÉDITABLE
    # =========================
    st.markdown("### ✏️ Modifier les écritures")

    edited_df = st.data_editor(
        df,
        use_container_width=True,
        num_rows="fixed",
        key="depenses_editor"
    )

    # =========================
    # SAUVEGARDE
    # =========================
    if not edited_df.equals(df):
        if st.button("💾 Enregistrer les modifications", type="primary"):
            changes = edited_df.merge(
                df,
                on="depense_id",
                suffixes=("_new", "_old")
            )

            modified = changes[
                (changes["date_new"] != changes["date_old"]) |
                (changes["compte_new"] != changes["compte_old"]) |
                (changes["poste_new"] != changes["poste_old"]) |
                (changes["fournisseur_new"] != changes["fournisseur_old"]) |
                (changes["montant_ttc_new"] != changes["montant_ttc_old"]) |
                (changes["lot_id_new"] != changes["lot_id_old"]) |
                (changes["commentaire_new"] != changes["commentaire_old"])
            ]

            for _, row in modified.iterrows():
                (
                    supabase
                    .table("depenses")
                    .update({
                        "date": row["date_new"],
                        "compte": row["compte_new"],
                        "poste": row["poste_new"],
                        "fournisseur": row["fournisseur_new"],
                        "montant_ttc": row["montant_ttc_new"],
                        "lot_id": row["lot_id_new"],
                        "commentaire": row["commentaire_new"],
                    })
                    .eq("depense_id", row["depense_id"])
                    .execute()
                )

            st.success(f"✅ {len(modified)} écriture(s) mise(s) à jour")
            st.rerun()