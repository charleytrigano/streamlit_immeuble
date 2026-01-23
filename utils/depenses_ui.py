import streamlit as st
import pandas as pd
from datetime import date

# ======================================================
# UI – ÉTAT DES DÉPENSES
# ======================================================
def depenses_ui(supabase):

    st.title("📋 État des dépenses")

    # -------------------------
    # Chargement des données
    # -------------------------
    res = supabase.table("depenses").select("*").execute()
    df = pd.DataFrame(res.data or [])

    if not df.empty:
        df["annee"] = df["annee"].astype(int)
        df["compte"] = df["compte"].astype(str)
        df["montant_ttc"] = df["montant_ttc"].astype(float)

    # -------------------------
    # Année (toujours visible)
    # -------------------------
    annees = sorted(df["annee"].unique()) if not df.empty else [2023, 2024, 2025, 2026]
    annee = st.selectbox("Année", annees)

    df_year = df[df["annee"] == annee] if not df.empty else pd.DataFrame()

    # -------------------------
    # KPI
    # -------------------------
    total = df_year["montant_ttc"].sum() if not df_year.empty else 0.0
    nb = len(df_year)
    moyenne = total / nb if nb else 0.0

    c1, c2, c3 = st.columns(3)
    c1.metric("Total dépenses (€)", f"{total:,.2f}")
    c2.metric("Nombre de lignes", nb)
    c3.metric("Dépense moyenne (€)", f"{moyenne:,.2f}")

    # -------------------------
    # Onglets
    # -------------------------
    tab_view, tab_add, tab_edit, tab_delete = st.tabs(
        ["📊 Consulter", "➕ Ajouter", "✏️ Modifier", "🗑 Supprimer"]
    )

    # ==================================================
    # CONSULTER
    # ==================================================
    with tab_view:
        if df_year.empty:
            st.info("Aucune dépense pour cette année.")
        else:
            st.dataframe(
                df_year.sort_values("date", ascending=False),
                use_container_width=True,
                hide_index=True,
            )

    # ==================================================
    # AJOUTER
    # ==================================================
    with tab_add:
        st.subheader("Ajouter une dépense")

        with st.form("add_depense"):
            d_date = st.date_input("Date", value=date.today())
            compte = st.text_input("Compte")
            poste = st.text_input("Poste")
            fournisseur = st.text_input("Fournisseur")
            montant = st.number_input("Montant TTC (€)", step=10.0)
            pdf_url = st.text_input("Lien facture (optionnel)")

            submitted = st.form_submit_button("Enregistrer")

        if submitted:
            if not compte or not poste:
                st.error("Compte et poste sont obligatoires.")
            else:
                supabase.table("depenses").insert({
                    "annee": annee,
                    "date": d_date.isoformat(),
                    "compte": compte,
                    "poste": poste,
                    "fournisseur": fournisseur,
                    "montant_ttc": montant,
                    "pdf_url": pdf_url,
                }).execute()

                st.success("Dépense ajoutée.")
                st.rerun()

    # ==================================================
    # MODIFIER
    # ==================================================
    with tab_edit:
        if df_year.empty:
            st.info("Aucune dépense à modifier.")
        else:
            row = st.selectbox(
                "Sélectionner une dépense",
                df_year.to_dict("records"),
                format_func=lambda x: f"{x['date']} – {x['poste']} – {x['montant_ttc']} €"
            )

            with st.form("edit_depense"):
                new_montant = st.number_input(
                    "Montant TTC (€)",
                    value=float(row["montant_ttc"]),
                    step=10.0,
                )
                submitted = st.form_submit_button("Mettre à jour")

            if submitted:
                supabase.table("depenses").update(
                    {"montant_ttc": new_montant}
                ).eq("id", row["id"]).execute()

                st.success("Dépense modifiée.")
                st.rerun()

    # ==================================================
    # SUPPRIMER
    # ==================================================
    with tab_delete:
        if df_year.empty:
            st.info("Aucune dépense à supprimer.")
        else:
            row = st.selectbox(
                "Dépense à supprimer",
                df_year.to_dict("records"),
                format_func=lambda x: f"{x['date']} – {x['poste']} – {x['montant_ttc']} €"
            )

            st.warning("Suppression définitive.")

            if st.button("Supprimer"):
                supabase.table("depenses").delete().eq("id", row["id"]).execute()
                st.success("Dépense supprimée.")
                st.rerun()