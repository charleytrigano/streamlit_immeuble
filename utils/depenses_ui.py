import streamlit as st
import pandas as pd
from datetime import date


def depenses_ui(supabase):
    st.title("📋 État des dépenses")

    # =========================
    # Sélecteur d'année
    # =========================
    res_years = supabase.table("depenses").select("annee").execute()
    years = sorted({r["annee"] for r in res_years.data if r["annee"] is not None})

    if not years:
        st.warning("Aucune dépense enregistrée.")
        return

    annee = st.selectbox("Année", years, index=len(years) - 1)

    # =========================
    # Chargement des données
    # =========================
    res = (
        supabase.table("depenses")
        .select("*")
        .eq("annee", annee)
        .order("date", desc=False)
        .execute()
    )

    df = pd.DataFrame(res.data)

    # =========================
    # KPI
    # =========================
    col1, col2, col3 = st.columns(3)

    total = float(df["montant_ttc"].sum()) if not df.empty else 0.0
    nb = len(df)
    moyenne = total / nb if nb else 0.0

    col1.metric("Total dépenses (€)", f"{total:,.2f}")
    col2.metric("Nombre de lignes", nb)
    col3.metric("Dépense moyenne (€)", f"{moyenne:,.2f}")

    # =========================
    # Onglets
    # =========================
    tab_consult, tab_add, tab_edit, tab_delete = st.tabs(
        ["📊 Consulter", "➕ Ajouter", "✏️ Modifier", "🗑 Supprimer"]
    )

    # =========================
    # CONSULTER
    # =========================
    with tab_consult:
        st.dataframe(df, use_container_width=True)

    # =========================
    # AJOUTER
    # =========================
    with tab_add:
        st.subheader("Ajouter une dépense")

        with st.form("add_depense_form", clear_on_submit=True):
            d = st.date_input("Date", value=date.today())
            compte = st.text_input("Compte")
            poste = st.text_input("Poste")
            fournisseur = st.text_input("Fournisseur")
            montant = st.number_input("Montant TTC (€)", min_value=0.0, step=0.01)
            lien = st.text_input("Lien facture (optionnel)")
            type_dep = st.text_input("Type (optionnel)")

            submit = st.form_submit_button("Enregistrer")

            if submit:
                payload = {
                    "annee": int(d.year),
                    "date": d.isoformat(),            # JSON SAFE
                    "compte": str(compte),
                    "poste": str(poste),
                    "fournisseur": str(fournisseur),
                    "montant_ttc": float(montant),
                    "lien_facture": lien if lien else None,
                    "type": type_dep if type_dep else None,
                }

                try:
                    supabase.table("depenses").insert(payload).execute()
                    st.success("Dépense enregistrée.")
                    st.rerun()
                except Exception as e:
                    st.error("Erreur lors de l’enregistrement")
                    st.code(str(e))

    # =========================
    # MODIFIER
    # =========================
    with tab_edit:
        if df.empty:
            st.info("Aucune dépense à modifier.")
        else:
            id_edit = st.selectbox(
                "Sélectionner une dépense",
                df["id"].tolist(),
                key="edit_id"
            )

            row = df[df["id"] == id_edit].iloc[0]

            with st.form("edit_depense_form"):
                d = st.date_input("Date", value=pd.to_datetime(row["date"]).date())
                compte = st.text_input("Compte", row["compte"])
                poste = st.text_input("Poste", row["poste"])
                fournisseur = st.text_input("Fournisseur", row["fournisseur"])
                montant = st.number_input(
                    "Montant TTC (€)",
                    min_value=0.0,
                    step=0.01,
                    value=float(row["montant_ttc"]),
                )
                lien = st.text_input("Lien facture", row.get("lien_facture") or "")
                type_dep = st.text_input("Type", row.get("type") or "")

                submit = st.form_submit_button("Mettre à jour")

                if submit:
                    payload = {
                        "annee": int(d.year),
                        "date": d.isoformat(),
                        "compte": str(compte),
                        "poste": str(poste),
                        "fournisseur": str(fournisseur),
                        "montant_ttc": float(montant),
                        "lien_facture": lien if lien else None,
                        "type": type_dep if type_dep else None,
                    }

                    try:
                        supabase.table("depenses").update(payload).eq("id", id_edit).execute()
                        st.success("Dépense mise à jour.")
                        st.rerun()
                    except Exception as e:
                        st.error("Erreur de mise à jour")
                        st.code(str(e))

    # =========================
    # SUPPRIMER
    # =========================
    with tab_delete:
        if df.empty:
            st.info("Aucune dépense à supprimer.")
        else:
            id_del = st.selectbox(
                "Sélectionner une dépense",
                df["id"].tolist(),
                key="delete_id"
            )

            if st.button("Supprimer définitivement"):
                try:
                    supabase.table("depenses").delete().eq("id", id_del).execute()
                    st.success("Dépense supprimée.")
                    st.rerun()
                except Exception as e:
                    st.error("Erreur de suppression")
                    st.code(str(e))