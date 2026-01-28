import streamlit as st
import pandas as pd
from datetime import date


def depenses_ui(supabase):
    st.title("📄 État des dépenses")

    # =============================
    # CHARGEMENT
    # =============================
    try:
        res = (
            supabase
            .table("depenses")
            .select("*")
            .order("date", desc=True)
            .execute()
        )
        df = pd.DataFrame(res.data or [])
    except Exception as e:
        st.error("Erreur de chargement des dépenses")
        st.exception(e)
        return

    if df.empty:
        st.warning("Aucune dépense trouvée")
        return

    # =============================
    # NORMALISATION
    # =============================
    if "date" in df.columns:
        df["date"] = pd.to_datetime(df["date"], errors="coerce")

    # =============================
    # KPI
    # =============================
    total = df["montant_ttc"].sum()
    c1, c2 = st.columns(2)
    c1.metric("Total dépenses TTC", f"{total:,.2f} €".replace(",", " "))
    c2.metric("Nombre de lignes", len(df))

    st.divider()

    # =============================
    # TABLEAU
    # =============================
    colonnes = [
        "depense_id",
        "annee",
        "compte",
        "poste",
        "fournisseur",
        "date",
        "montant_ttc",
        "type",
        "commentaire"
    ]
    colonnes = [c for c in colonnes if c in df.columns]

    st.dataframe(
        df[colonnes].sort_values("date", ascending=False),
        use_container_width=True
    )

    st.divider()

    # =============================
    # MODE
    # =============================
    mode = st.radio(
        "Action",
        ["➕ Ajouter", "✏️ Modifier", "❌ Supprimer"],
        horizontal=True
    )

    # =============================
    # AJOUT
    # =============================
    if mode == "➕ Ajouter":
        st.subheader("Ajouter une dépense")

        with st.form("add_depense"):
            annee = st.number_input("Année", value=date.today().year)
            compte = st.text_input("Compte")
            poste = st.text_input("Poste")
            fournisseur = st.text_input("Fournisseur")
            d = st.date_input("Date", value=date.today())
            montant = st.number_input("Montant TTC", step=0.01)
            type_dep = st.text_input("Type (Charge, Assurance, Agios, etc.)")
            commentaire = st.text_area("Commentaire")

            submit = st.form_submit_button("Ajouter")

        if submit:
            supabase.table("depenses").insert({
                "annee": annee,
                "compte": compte,
                "poste": poste,
                "fournisseur": fournisseur,
                "date": d.isoformat(),
                "montant_ttc": montant,
                "type": type_dep,
                "commentaire": commentaire
            }).execute()

            st.success("Dépense ajoutée")
            st.experimental_rerun()

    # =============================
    # MODIFICATION
    # =============================
    if mode == "✏️ Modifier":
        st.subheader("Modifier une dépense")

        depense_id = st.selectbox(
            "Sélectionner une dépense",
            df["depense_id"],
            format_func=lambda x: f"ID {x}"
        )

        dep = df[df["depense_id"] == depense_id].iloc[0]

        with st.form("edit_depense"):
            annee = st.number_input("Année", value=int(dep["annee"]))
            compte = st.text_input("Compte", dep["compte"])
            poste = st.text_input("Poste", dep["poste"])
            fournisseur = st.text_input("Fournisseur", dep["fournisseur"])
            d = st.date_input("Date", dep["date"].date() if pd.notnull(dep["date"]) else date.today())
            montant = st.number_input("Montant TTC", value=float(dep["montant_ttc"]), step=0.01)
            type_dep = st.text_input("Type", dep["type"])
            commentaire = st.text_area("Commentaire", dep.get("commentaire", ""))

            submit = st.form_submit_button("Enregistrer")

        if submit:
            supabase.table("depenses").update({
                "annee": annee,
                "compte": compte,
                "poste": poste,
                "fournisseur": fournisseur,
                "date": d.isoformat(),
                "montant_ttc": montant,
                "type": type_dep,
                "commentaire": commentaire
            }).eq("depense_id", depense_id).execute()

            st.success("Dépense modifiée")
            st.experimental_rerun()

    # =============================
    # SUPPRESSION
    # =============================
    if mode == "❌ Supprimer":
        st.subheader("Supprimer une dépense")

        depense_id = st.selectbox(
            "Sélectionner une dépense à supprimer",
            df["depense_id"]
        )

        st.warning("⚠️ Cette action est irréversible")

        if st.button("Supprimer définitivement"):
            supabase.table("depenses") \
                .delete() \
                .eq("depense_id", depense_id) \
                .execute()

            st.success("Dépense supprimée")
            st.experimental_rerun()