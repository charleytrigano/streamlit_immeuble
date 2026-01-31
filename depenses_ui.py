import streamlit as st
import pandas as pd
from datetime import date
import uuid

# =========================
# FORMAT €
# =========================
def euro(x):
    try:
        return f"{float(x):,.2f} €".replace(",", " ").replace(".", ",")
    except Exception:
        return x


# =========================
# UI DÉPENSES
# =========================
def depenses_ui(supabase, annee):

    st.header(f"📄 État des dépenses – {annee}")

    # =========================
    # CHARGEMENT DES DONNÉES
    # =========================
    res = (
        supabase
        .table("depenses")
        .select("*")
        .eq("annee", annee)
        .order("date", desc=False)
        .execute()
    )

    if not res.data:
        st.info("Aucune dépense pour cette année")
        return

    df = pd.DataFrame(res.data)

    # =========================
    # FILTRES
    # =========================
    with st.expander("🔎 Filtres", expanded=True):
        col1, col2, col3, col4 = st.columns(4)

        compte_f = col1.selectbox(
            "Compte",
            ["Tous"] + sorted(df["compte"].dropna().unique().tolist())
        )

        poste_f = col2.selectbox(
            "Poste",
            ["Tous"] + sorted(df["poste"].dropna().unique().tolist())
        )

        fournisseur_f = col3.selectbox(
            "Fournisseur",
            ["Tous"] + sorted(df["fournisseur"].dropna().unique().tolist())
        )

        lot_f = col4.selectbox(
            "Lot",
            ["Tous"] + sorted(df["lot_id"].dropna().astype(str).unique().tolist())
        )

    df_f = df.copy()

    if compte_f != "Tous":
        df_f = df_f[df_f["compte"] == compte_f]

    if poste_f != "Tous":
        df_f = df_f[df_f["poste"] == poste_f]

    if fournisseur_f != "Tous":
        df_f = df_f[df_f["fournisseur"] == fournisseur_f]

    if lot_f != "Tous":
        df_f = df_f[df_f["lot_id"].astype(str) == lot_f]

    # =========================
    # KPI
    # =========================
    c1, c2, c3 = st.columns(3)
    c1.metric("Total dépenses", euro(df_f["montant_ttc"].sum()))
    c2.metric("Nombre de lignes", int(len(df_f)))
    c3.metric(
        "Dépense moyenne",
        euro(df_f["montant_ttc"].mean() if len(df_f) else 0)
    )

    st.divider()

    # =========================
    # AJOUT DÉPENSE
    # =========================
    with st.expander("➕ Ajouter une dépense"):
        with st.form("add_depense"):
            col1, col2, col3 = st.columns(3)

            new_date = col1.date_input("Date", value=date.today())
            new_compte = col2.text_input("Compte")
            new_poste = col3.text_input("Poste")

            col4, col5, col6 = st.columns(3)
            new_fournisseur = col4.text_input("Fournisseur")
            new_montant = col5.number_input("Montant TTC", min_value=0.0, step=10.0)
            new_lot = col6.number_input("Lot ID", step=1)

            new_commentaire = st.text_area("Commentaire")

            if st.form_submit_button("➕ Ajouter"):
                supabase.table("depenses").insert({
                    "depense_id": str(uuid.uuid4()),
                    "annee": annee,
                    "date": new_date.isoformat(),
                    "compte": new_compte,
                    "poste": new_poste,
                    "fournisseur": new_fournisseur,
                    "montant_ttc": new_montant,
                    "lot_id": int(new_lot) if new_lot else None,
                    "commentaire": new_commentaire,
                }).execute()

                st.success("Dépense ajoutée")
                st.rerun()

    st.divider()

    # =========================
    # TABLE CONFORT
    # =========================
    display_cols = [
        "depense_id",
        "date",
        "compte",
        "poste",
        "fournisseur",
        "montant_ttc",
        "lot_id",
        "commentaire",
    ]

    df_disp = df_f[display_cols].copy()

    df_disp["montant_ttc"] = df_disp["montant_ttc"].apply(euro)

    st.markdown("### 📋 Dépenses")

    selected = st.dataframe(
        df_disp,
        use_container_width=True,
        hide_index=True,
    )

    st.divider()

    # =========================
    # MODIFIER / SUPPRIMER
    # =========================
    st.markdown("### ✏️ Modifier / 🗑️ Supprimer une dépense")

    dep_ids = df_f["depense_id"].tolist()

    selected_id = st.selectbox(
        "Sélectionner une dépense",
        dep_ids,
        format_func=lambda x: f"{x}"
    )

    dep = df_f[df_f["depense_id"] == selected_id].iloc[0]

    with st.form("edit_depense"):
        col1, col2, col3 = st.columns(3)

        e_date = col1.date_input("Date", value=pd.to_datetime(dep["date"]))
        e_compte = col2.text_input("Compte", dep["compte"])
        e_poste = col3.text_input("Poste", dep["poste"])

        col4, col5, col6 = st.columns(3)
        e_fournisseur = col4.text_input("Fournisseur", dep["fournisseur"])
        e_montant = col5.number_input(
            "Montant TTC",
            value=float(dep["montant_ttc"]),
            step=10.0
        )
        e_lot = col6.number_input(
            "Lot ID",
            value=int(dep["lot_id"]) if dep["lot_id"] else 0,
            step=1
        )

        e_commentaire = st.text_area("Commentaire", dep["commentaire"])

        col_btn1, col_btn2 = st.columns(2)

        if col_btn1.form_submit_button("💾 Enregistrer"):
            supabase.table("depenses").update({
                "date": e_date.isoformat(),
                "compte": e_compte,
                "poste": e_poste,
                "fournisseur": e_fournisseur,
                "montant_ttc": e_montant,
                "lot_id": int(e_lot) if e_lot else None,
                "commentaire": e_commentaire,
            }).eq("depense_id", selected_id).execute()

            st.success("Dépense mise à jour")
            st.rerun()

        if col_btn2.form_submit_button("🗑️ Supprimer"):
            supabase.table("depenses").delete().eq(
                "depense_id", selected_id
            ).execute()

            st.warning("Dépense supprimée")
            st.rerun()
