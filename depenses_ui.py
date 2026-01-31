import streamlit as st
import pandas as pd
from datetime import date


def euro(x):
    return f"{x:,.2f} €".replace(",", " ").replace(".", ",")


def depenses_ui(supabase, annee):
    st.header(f"📄 Dépenses – {annee}")

    # ======================================================
    # CHARGEMENT DES DONNÉES (VUE)
    # ======================================================
    resp = (
        supabase
        .table("v_depenses_enrichies")
        .select("*")
        .eq("annee", annee)
        .execute()
    )

    if not resp.data:
        st.info("Aucune dépense pour cette année.")
        df = pd.DataFrame()
    else:
        df = pd.DataFrame(resp.data)

    # Normalisation
    if not df.empty:
        df["montant_ttc"] = pd.to_numeric(df["montant_ttc"], errors="coerce").fillna(0)

    has_fournisseur = "fournisseur" in df.columns

    # ======================================================
    # FILTRES
    # ======================================================
    st.subheader("🔎 Filtres")

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        groupes = ["Tous"] + sorted(df["groupe_charges"].dropna().unique().tolist()) if not df.empty else ["Tous"]
        groupe_sel = st.selectbox("Groupe de charges", groupes)

    with col2:
        comptes = ["Tous"]
        if not df.empty:
            comptes += sorted(
                df[["compte", "libelle_compte"]]
                .dropna()
                .drop_duplicates()
                .apply(lambda x: f"{x['compte']} – {x['libelle_compte']}", axis=1)
                .tolist()
            )
        compte_sel = st.selectbox("Compte", comptes)

    with col3:
        postes = ["Tous"] + sorted(df["poste"].dropna().unique().tolist()) if not df.empty else ["Tous"]
        poste_sel = st.selectbox("Poste", postes)

    with col4:
        if has_fournisseur:
            fournisseurs = ["Tous"] + sorted(df["fournisseur"].dropna().unique().tolist())
            fournisseur_sel = st.selectbox("Fournisseur", fournisseurs)
        else:
            fournisseur_sel = "Tous"
            st.caption("Fournisseur non disponible")

    # ======================================================
    # APPLICATION DES FILTRES
    # ======================================================
    df_f = df.copy()

    if groupe_sel != "Tous":
        df_f = df_f[df_f["groupe_charges"] == groupe_sel]

    if compte_sel != "Tous":
        code = compte_sel.split(" – ")[0]
        df_f = df_f[df_f["compte"] == code]

    if poste_sel != "Tous":
        df_f = df_f[df_f["poste"] == poste_sel]

    if has_fournisseur and fournisseur_sel != "Tous":
        df_f = df_f[df_f["fournisseur"] == fournisseur_sel]

    # ======================================================
    # KPI
    # ======================================================
    st.subheader("📊 Indicateurs")

    total_dep = df_f["montant_ttc"].sum() if not df_f.empty else 0
    nb_lignes = len(df_f)
    dep_moy = total_dep / nb_lignes if nb_lignes else 0

    k1, k2, k3 = st.columns(3)
    k1.metric("💸 Total dépenses", euro(total_dep))
    k2.metric("🧾 Nombre de lignes", nb_lignes)
    k3.metric("📊 Dépense moyenne", euro(dep_moy))

    # ======================================================
    # DÉPENSES PAR GROUPE
    # ======================================================
    st.subheader("📊 Dépenses par groupe de charges")

    if not df_f.empty:
        df_group = (
            df_f
            .groupby("groupe_charges", as_index=False)
            .agg(total=("montant_ttc", "sum"))
            .sort_values("groupe_charges")
        )
        df_group["total"] = df_group["total"].apply(euro)
        st.dataframe(df_group, use_container_width=True)
    else:
        st.info("Aucune donnée à afficher.")

    # ======================================================
    # DÉTAIL DES DÉPENSES
    # ======================================================
    st.subheader("📋 Détail des dépenses")

    if not df_f.empty:
        df_detail = df_f[[
            "depense_id",
            "date",
            "compte",
            "libelle_compte",
            "poste",
            "montant_ttc",
            "groupe_charges"
        ]].copy()

        df_detail["montant_ttc"] = df_detail["montant_ttc"].apply(euro)

        st.dataframe(df_detail, use_container_width=True)

    # ======================================================
    # AJOUT / MODIFICATION / SUPPRESSION
    # ======================================================
    st.divider()
    st.subheader("✏️ Gestion des dépenses")

    with st.expander("➕ Ajouter une dépense"):
        with st.form("add_depense"):
            d_date = st.date_input("Date", value=date.today())
            d_compte = st.text_input("Compte (8 chiffres)")
            d_poste = st.text_input("Poste")
            d_montant = st.number_input("Montant TTC", min_value=0.0, step=10.0)
            d_fournisseur = st.text_input("Fournisseur")
            submitted = st.form_submit_button("Ajouter")

            if submitted:
                supabase.table("depenses").insert({
                    "annee": annee,
                    "date": d_date.isoformat(),
                    "compte": d_compte,
                    "poste": d_poste,
                    "montant_ttc": d_montant,
                    "fournisseur": d_fournisseur
                }).execute()
                st.success("Dépense ajoutée")
                st.rerun()

    if not df_f.empty:
        with st.expander("✏️ Modifier / Supprimer une dépense"):
            dep_id = st.selectbox(
                "Sélectionner une dépense",
                df_f["depense_id"].tolist()
            )

            dep_row = df_f[df_f["depense_id"] == dep_id].iloc[0]

            d_poste = st.text_input("Poste", dep_row["poste"])
            d_montant = st.number_input(
                "Montant TTC",
                value=float(dep_row["montant_ttc"]),
                step=10.0
            )

            colA, colB = st.columns(2)

            with colA:
                if st.button("💾 Enregistrer"):
                    supabase.table("depenses").update({
                        "poste": d_poste,
                        "montant_ttc": d_montant
                    }).eq("id", dep_id).execute()
                    st.success("Dépense mise à jour")
                    st.rerun()

            with colB:
                if st.button("🗑️ Supprimer"):
                    supabase.table("depenses").delete().eq("id", dep_id).execute()
                    st.warning("Dépense supprimée")
                    st.rerun()