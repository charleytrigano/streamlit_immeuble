import streamlit as st
import pandas as pd
from datetime import date


def depenses_ui(supabase, annee):
    st.header(f"📄 Dépenses – {annee}")

    # ======================================================
    # CHARGEMENT DES DÉPENSES (TABLE depenses UNIQUEMENT)
    # ======================================================
    resp = (
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
        .order("date", desc=False)
        .execute()
    )

    if not resp.data:
        st.info("Aucune dépense pour cette année.")
        return

    df = pd.DataFrame(resp.data)

    # ======================================================
    # FILTRES
    # ======================================================
    st.subheader("🔎 Filtres")

    colf1, colf2 = st.columns(2)

    with colf1:
        fournisseurs = ["Tous"] + sorted(
            df["fournisseur"].dropna().unique().tolist()
        )
        fournisseur_sel = st.selectbox("Fournisseur", fournisseurs)

    with colf2:
        comptes = ["Tous"] + sorted(
            df["compte"].dropna().unique().tolist()
        )
        compte_sel = st.selectbox("Compte", comptes)

    df_f = df.copy()

    if fournisseur_sel != "Tous":
        df_f = df_f[df_f["fournisseur"] == fournisseur_sel]

    if compte_sel != "Tous":
        df_f = df_f[df_f["compte"] == compte_sel]

    # ======================================================
    # TABLEAU DES DÉPENSES (depense_id CACHÉ)
    # ======================================================
    st.subheader("📋 Détail des dépenses")

    df_view = df_f[[
        "date",
        "compte",
        "poste",
        "fournisseur",
        "montant_ttc",
        "lot_id",
        "commentaire",
        "depense_id",   # gardé uniquement pour les actions
    ]]

    st.dataframe(
        df_view.drop(columns=["depense_id"]),
        use_container_width=True
    )

    # ======================================================
    # AJOUT D'UNE DÉPENSE
    # ======================================================
    st.divider()
    st.subheader("➕ Ajouter une dépense")

    with st.form("add_depense"):
        c1, c2, c3 = st.columns(3)

        with c1:
            d_date = st.date_input("Date", value=date.today())
            d_compte = st.text_input("Compte")

        with c2:
            d_poste = st.text_input("Poste")
            d_fournisseur = st.text_input("Fournisseur")

        with c3:
            d_montant = st.number_input("Montant TTC", min_value=0.0, step=10.0)
            d_lot = st.number_input("Lot", min_value=0, step=1)

        d_commentaire = st.text_input("Commentaire")

        submitted = st.form_submit_button("➕ Ajouter")

        if submitted:
            supabase.table("depenses").insert({
                "annee": annee,
                "date": d_date.isoformat(),
                "compte": d_compte,
                "poste": d_poste,
                "fournisseur": d_fournisseur,
                "montant_ttc": d_montant,
                "lot_id": d_lot,
                "commentaire": d_commentaire
            }).execute()

            st.success("✅ Dépense ajoutée")
            st.rerun()

    # ======================================================
    # MODIFIER / SUPPRIMER UNE DÉPENSE
    # ======================================================
    st.divider()
    st.subheader("✏️ Modifier / 🗑 Supprimer une dépense")

    options = {
        f"{row['date']} | {row['fournisseur']} | {row['montant_ttc']} €": row
        for _, row in df_f.iterrows()
    }

    if not options:
        st.info("Aucune dépense sélectionnable.")
        return

    selected_label = st.selectbox(
        "Sélectionne une dépense",
        options=list(options.keys())
    )

    dep = options[selected_label]

    with st.form("edit_depense"):
        c1, c2, c3 = st.columns(3)

        with c1:
            e_date = st.date_input("Date", value=pd.to_datetime(dep["date"]))
            e_compte = st.text_input("Compte", value=dep["compte"])

        with c2:
            e_poste = st.text_input("Poste", value=dep["poste"])
            e_fournisseur = st.text_input("Fournisseur", value=dep["fournisseur"])

        with c3:
            e_montant = st.number_input(
                "Montant TTC",
                min_value=0.0,
                step=10.0,
                value=float(dep["montant_ttc"])
            )
            e_lot = st.number_input(
                "Lot",
                min_value=0,
                step=1,
                value=int(dep["lot_id"]) if dep["lot_id"] else 0
            )

        e_commentaire = st.text_input(
            "Commentaire",
            value=dep["commentaire"] or ""
        )

        colb1, colb2 = st.columns(2)

        with colb1:
            save = st.form_submit_button("💾 Enregistrer")

        with colb2:
            delete = st.form_submit_button("🗑 Supprimer")

        if save:
            supabase.table("depenses").update({
                "date": e_date.isoformat(),
                "compte": e_compte,
                "poste": e_poste,
                "fournisseur": e_fournisseur,
                "montant_ttc": e_montant,
                "lot_id": e_lot,
                "commentaire": e_commentaire
            }).eq("depense_id", dep["depense_id"]).execute()

            st.success("✅ Dépense modifiée")
            st.rerun()

        if delete:
            supabase.table("depenses") \
                .delete() \
                .eq("depense_id", dep["depense_id"]) \
                .execute()

            st.success("🗑 Dépense supprimée")
            st.rerun()