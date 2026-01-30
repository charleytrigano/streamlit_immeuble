import streamlit as st
import pandas as pd

def depenses_ui(supabase, annee):
    st.subheader(f"📄 Dépenses – {annee}")

    # =========================
    # Chargement des dépenses
    # =========================
    res = (
        supabase
        .table("depenses")
        .select("""
            id,
            date_depense,
            compte_8,
            poste,
            montant_ttc,
            lot_id,
            commentaire
        """)
        .eq("annee", annee)
        .order("date_depense")
        .execute()
    )

    if not res.data:
        st.info("Aucune dépense pour cette année")
        return

    df = pd.DataFrame(res.data)

    # =========================
    # Table éditable
    # =========================
    st.markdown("### ✏️ Modifier les écritures")

    edited_df = st.data_editor(
        df,
        use_container_width=True,
        num_rows="fixed",
        key="depenses_editor"
    )

    # =========================
    # Détection des modifications
    # =========================
    if not edited_df.equals(df):
        if st.button("💾 Enregistrer les modifications"):
            changes = edited_df.merge(
                df,
                on="id",
                suffixes=("_new", "_old")
            )

            modified = changes[
                (changes["compte_8_new"] != changes["compte_8_old"]) |
                (changes["poste_new"] != changes["poste_old"]) |
                (changes["montant_ttc_new"] != changes["montant_ttc_old"]) |
                (changes["lot_id_new"] != changes["lot_id_old"]) |
                (changes["commentaire_new"] != changes["commentaire_old"]) |
                (changes["date_depense_new"] != changes["date_depense_old"])
            ]

            for _, row in modified.iterrows():
                (
                    supabase
                    .table("depenses")
                    .update({
                        "date_depense": row["date_depense_new"],
                        "compte_8": row["compte_8_new"],
                        "poste": row["poste_new"],
                        "montant_ttc": row["montant_ttc_new"],
                        "lot_id": row["lot_id_new"],
                        "commentaire": row["commentaire_new"],
                    })
                    .eq("id", row["id"])
                    .execute()
                )

            st.success(f"✅ {len(modified)} écriture(s) mise(s) à jour")
            st.rerun()