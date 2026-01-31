import streamlit as st
import pandas as pd


def lots_ui(supabase):
    st.header("🏢 Lots")
    

    # =========================
    # Chargement des lots
    # =========================
    try:
        res = (
            supabase
            .table("lots")
            .select(
                "lot, tantiemes, etage, usage, description, proprietaire, locataire"
            )
            .order("lot")
            .execute()
        )
        df = pd.DataFrame(res.data or [])
    except Exception as e:
        st.error(f"Erreur chargement lots : {e}")
        return

    if df.empty:
        st.info("Aucun lot trouvé.")
        return

    # =========================
    # Tableau des lots
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

    lot_sel = st.selectbox(
        "Lot",
        df["lot"].tolist()
    )

    row = df[df["lot"] == lot_sel].iloc[0]

    # =========================
    # Formulaire édition
    # =========================
    with st.form("edit_lot_form"):
        c1, c2, c3 = st.columns(3)

        with c1:
            tantiemes = st.number_input(
                "Tantièmes",
                value=0 if pd.isna(row["tantiemes"]) else float(row["tantiemes"]),
                step=1.0
            )
            etage = st.text_input(
                "Étage",
                value="" if pd.isna(row["etage"]) else row["etage"]
            )

        with c2:
            usage = st.text_input(
                "Usage",
                value="" if pd.isna(row["usage"]) else row["usage"]
            )
            proprietaire = st.text_input(
                "Propriétaire",
                value="" if pd.isna(row["proprietaire"]) else row["proprietaire"]
            )

        with c3:
            locataire = st.text_input(
                "Locataire",
                value="" if pd.isna(row["locataire"]) else row["locataire"]
            )

        description = st.text_area(
            "Description",
            value="" if pd.isna(row["description"]) else row["description"]
        )

        submit = st.form_submit_button("💾 Enregistrer")

    # =========================
    # Sauvegarde
    # =========================
    if submit:
        try:
            supabase.table("lots").update({
                "tantiemes": tantiemes,
                "etage": etage or None,
                "usage": usage or None,
                "description": description or None,
                "proprietaire": proprietaire or None,
                "locataire": locataire or None,
            }).eq("lot", lot_sel).execute()

            st.success(f"Lot {lot_sel} mis à jour.")
            st.rerun()

        except Exception as e:
            st.error(f"Erreur mise à jour : {e}")

    # =========================
    # Règles métier visibles
    # =========================
    st.divider()
    st.info(
        "🔒 Règles de gestion :\n"
        "- Les lots ne peuvent pas être ajoutés ni supprimés\n"
        "- Toutes les informations sont modifiables\n"
        "- Les champs peuvent être laissés vides"
    )
