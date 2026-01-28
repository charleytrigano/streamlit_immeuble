import streamlit as st
import pandas as pd


def lots_ui(supabase):
    st.title("🏢 Lots")
    st.caption("Gestion des lots – modification du propriétaire et du locataire uniquement")

    # =========================
    # Chargement des données
    # =========================
    try:
        res = (
            supabase
            .table("lots")
            .select("lot, tantiemes, proprietaire, locataire")
            .order("lot")
            .execute()
        )
        data = res.data or []
        df = pd.DataFrame(data)

    except Exception as e:
        st.error(f"Erreur chargement lots : {e}")
        return

    if df.empty:
        st.info("Aucun lot trouvé.")
        return

    # =========================
    # Affichage tableau
    # =========================
    st.subheader("📋 Liste des lots")

    st.dataframe(
        df,
        use_container_width=True,
        hide_index=True
    )

    st.divider()

    # =========================
    # Sélection du lot
    # =========================
    st.subheader("✏️ Modifier un lot")

    lot_selectionne = st.selectbox(
        "Lot",
        df["lot"].tolist()
    )

    lot_row = df[df["lot"] == lot_selectionne].iloc[0]

    # =========================
    # Formulaire modification
    # =========================
    with st.form("form_edit_lot"):
        col1, col2 = st.columns(2)

        with col1:
            proprietaire = st.text_input(
                "Propriétaire",
                value="" if pd.isna(lot_row["proprietaire"]) else lot_row["proprietaire"]
            )

        with col2:
            locataire = st.text_input(
                "Locataire",
                value="" if pd.isna(lot_row["locataire"]) else lot_row["locataire"]
            )

        submitted = st.form_submit_button("💾 Enregistrer")

    # =========================
    # Sauvegarde
    # =========================
    if submitted:
        try:
            supabase.table("lots").update({
                "proprietaire": proprietaire if proprietaire.strip() != "" else None,
                "locataire": locataire if locataire.strip() != "" else None
            }).eq("lot", lot_selectionne).execute()

            st.success(f"Lot {lot_selectionne} mis à jour avec succès.")
            st.experimental_rerun()

        except Exception as e:
            st.error(f"Erreur lors de la mise à jour : {e}")

    # =========================
    # Règles métier visibles
    # =========================
    st.divider()
    st.info(
        "🔒 Règles :\n"
        "- Les lots ne peuvent pas être supprimés\n"
        "- Les colonnes *Propriétaire* et *Locataire* sont modifiables\n"
        "- Les champs peuvent être laissés vides"
    )
