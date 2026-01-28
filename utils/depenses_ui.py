import streamlit as st
import pandas as pd
from datetime import date


# =========================
# UI ÉTAT DES DÉPENSES
# =========================
def depenses_ui(supabase):

    st.header("📄 État des dépenses")

    # =========================
    # CHARGEMENT DONNÉES
    # =========================
    resp = supabase.table("depenses").select("*").execute()
    df = pd.DataFrame(resp.data)

    if df.empty:
        st.warning("Aucune dépense enregistrée.")
        return

    # =========================
    # NORMALISATION
    # =========================
    df["annee"] = pd.to_numeric(df["annee"], errors="coerce")
    df["montant_ttc"] = pd.to_numeric(df["montant_ttc"], errors="coerce").fillna(0)
    df["date"] = pd.to_datetime(df["date"], errors="coerce")

    # =========================
    # FILTRES
    # =========================
    st.subheader("🔎 Filtres")

    colf1, colf2, colf3, colf4 = st.columns(4)

    with colf1:
        annee = st.selectbox(
            "Année",
            sorted(df["annee"].dropna().unique().tolist()),
        )

    df_f = df[df["annee"] == annee]

    with colf2:
        compte = st.selectbox(
            "Compte",
            ["Tous"] + sorted(df_f["compte"].dropna().unique().tolist())
        )

    if compte != "Tous":
        df_f = df_f[df_f["compte"] == compte]

    with colf3:
        fournisseur = st.selectbox(
            "Fournisseur",
            ["Tous"] + sorted(df_f["fournisseur"].dropna().unique().tolist())
        )

    if fournisseur != "Tous":
        df_f = df_f[df_f["fournisseur"] == fournisseur]

    with colf4:
        poste = st.selectbox(
            "Poste",
            ["Tous"] + sorted(df_f["poste"].dropna().unique().tolist())
        )

    if poste != "Tous":
        df_f = df_f[df_f["poste"] == poste]

    # =========================
    # KPI
    # =========================
    st.subheader("📊 Indicateurs")

    total_dep = df_f["montant_ttc"].sum()
    nb_dep = len(df_f)
    dep_moy = total_dep / nb_dep if nb_dep else 0

    col1, col2, col3 = st.columns(3)

    col1.metric("Total dépenses (€)", f"{total_dep:,.2f} €".replace(",", " ").replace(".", ","))
    col2.metric("Nombre de lignes", nb_dep)
    col3.metric("Dépense moyenne (€)", f"{dep_moy:,.2f} €".replace(",", " ").replace(".", ","))

    # =========================
    # TABLEAU
    # =========================
    st.subheader("📋 Liste des dépenses")

    df_display = df_f.copy()

    # Lien facture cliquable
    def make_link(row):
        if pd.notna(row["facture_url"]) and row["facture_url"]:
            return f"[Voir]({row['facture_url']})"
        if pd.notna(row["facture_path"]) and row["facture_path"]:
            return f"[Voir]({row['facture_path']})"
        return ""

    df_display["Facture"] = df_display.apply(make_link, axis=1)

    st.dataframe(
        df_display[
            [
                "date",
                "compte",
                "poste",
                "fournisseur",
                "montant_ttc",
                "type",
                "commentaire",
                "Facture",
            ]
        ].sort_values("date", ascending=False),
        use_container_width=True
    )

    # =========================
    # AJOUT
    # =========================
    st.subheader("➕ Ajouter une dépense")

    with st.form("add_depense"):
        c1, c2, c3 = st.columns(3)

        with c1:
            f_date = st.date_input("Date", value=date.today())
            f_compte = st.text_input("Compte")

        with c2:
            f_poste = st.text_input("Poste")
            f_fournisseur = st.text_input("Fournisseur")

        with c3:
            f_montant = st.number_input("Montant TTC", step=0.01)
            f_type = st.selectbox("Type", ["Charge", "Avoir", "Remboursement"])

        f_commentaire = st.text_area("Commentaire")
        f_facture_url = st.text_input("Lien facture (URL)")

        submit = st.form_submit_button("Enregistrer")

        if submit:
            supabase.table("depenses").insert({
                "annee": int(f_date.year),
                "date": f_date.isoformat(),
                "compte": f_compte,
                "poste": f_poste,
                "fournisseur": f_fournisseur,
                "montant_ttc": f_montant,
                "type": f_type,
                "commentaire": f_commentaire,
                "facture_url": f_facture_url,
            }).execute()

            st.success("Dépense ajoutée")
            st.rerun()

    # =========================
    # SUPPRESSION
    # =========================
    st.subheader("🗑 Supprimer une dépense")

    dep_id = st.selectbox(
        "Sélectionner une dépense",
        df_f["depense_id"].tolist(),
        format_func=lambda x: f"{x}"
    )

    if st.button("Supprimer"):
        supabase.table("depenses").delete().eq("depense_id", dep_id).execute()
        st.success("Dépense supprimée")
        st.rerun()