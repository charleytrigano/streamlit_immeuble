import streamlit as st
import pandas as pd


def etat_depenses_ui(supabase):

    tabs = st.tabs(
        ["📊 Consulter", "➕ Ajouter", "✏️ Modifier", "🗑 Supprimer"]
    )

    # ======================================================
    # 📊 CONSULTER
    # ======================================================
    with tabs[0]:
        st.subheader("📊 État des dépenses")

        # ---- Chargement ----
        df = supabase.table("depenses").select("*").execute().data
        df = pd.DataFrame(df)

        if df.empty:
            st.info("Aucune dépense enregistrée.")
            return

        # ---- Filtres ----
        col1, col2, col3 = st.columns(3)

        with col1:
            annee = st.selectbox(
                "Année",
                ["Toutes"] + sorted(df["annee"].unique().tolist())
            )

        with col2:
            fournisseur = st.selectbox(
                "Fournisseur",
                ["Tous"] + sorted(df["fournisseur"].dropna().unique().tolist())
            )

        with col3:
            compte = st.selectbox(
                "Compte",
                ["Tous"] + sorted(df["compte"].dropna().unique().tolist())
            )

        if annee != "Toutes":
            df = df[df["annee"] == annee]
        if fournisseur != "Tous":
            df = df[df["fournisseur"] == fournisseur]
        if compte != "Tous":
            df = df[df["compte"] == compte]

        # ---- KPIs ----
        c1, c2, c3 = st.columns(3)
        c1.metric("Dépenses totales (€)", f"{df['montant_ttc'].sum():,.2f}")
        c2.metric("Nombre de lignes", len(df))
        c3.metric("Moyenne (€)", f"{df['montant_ttc'].mean():,.2f}")

        # ---- Tableau ----
        st.dataframe(
            df.sort_values("date", ascending=False),
            use_container_width=True
        )

    # ======================================================
    # ➕ AJOUTER
    # ======================================================
    with tabs[1]:
        st.subheader("➕ Ajouter une dépense")

        with st.form("add_depense"):
            annee = st.number_input("Année", value=2025)
            compte = st.text_input("Compte")
            poste = st.text_input("Poste")
            fournisseur = st.text_input("Fournisseur")
            date = st.date_input("Date")
            montant = st.number_input("Montant TTC", step=0.01)
            piece_id = st.text_input("Pièce ID")
            pdf_url = st.text_input("Lien facture (Google Drive)")

            submitted = st.form_submit_button("Enregistrer")

        if submitted:
            supabase.table("depenses").insert({
                "annee": annee,
                "compte": compte,
                "poste": poste,
                "fournisseur": fournisseur,
                "date": str(date),
                "montant_ttc": montant,
                "piece_id": piece_id,
                "pdf_url": pdf_url,
            }).execute()

            st.success("Dépense ajoutée")

    # ======================================================
    # ✏️ MODIFIER
    # ======================================================
    with tabs[2]:
        st.subheader("✏️ Modifier une dépense")

        df = pd.DataFrame(
            supabase.table("depenses").select("*").execute().data
        )

        dep_id = st.selectbox(
            "Sélectionner une dépense",
            df["id"],
            format_func=lambda x: f"{x}"
        )

        dep = df[df["id"] == dep_id].iloc[0]

        montant = st.number_input(
            "Montant TTC",
            value=float(dep["montant_ttc"])
        )

        if st.button("Mettre à jour"):
            supabase.table("depenses") \
                .update({"montant_ttc": montant}) \
                .eq("id", dep_id) \
                .execute()

            st.success("Dépense mise à jour")

    # ======================================================
    # 🗑 SUPPRIMER
    # ======================================================
    with tabs[3]:
        st.subheader("🗑 Supprimer une dépense")

        dep_id = st.selectbox(
            "Dépense à supprimer",
            df["id"]
        )

        if st.button("Supprimer définitivement"):
            supabase.table("depenses") \
                .delete() \
                .eq("id", dep_id) \
                .execute()

            st.success("Dépense supprimée")
