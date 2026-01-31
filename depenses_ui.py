import streamlit as st
import pandas as pd


def depenses_ui(supabase, annee):
    st.header("💸 Dépenses")

    # ======================================================
    # Chargement des données (SOURCE UNIQUE)
    # ======================================================
    resp = (
        supabase
        .table("v_depenses_enrichies")
        .select(
            "date, annee, montant_ttc, fournisseur, "
            "compte, libelle_compte, "
            "groupe_charges, libelle_groupe"
        )
        .eq("annee", annee)
        .execute()
    )

    if not resp.data:
        st.warning("Aucune dépense pour cette année.")
        return

    df = pd.DataFrame(resp.data)

    # ======================================================
    # NORMALISATION DES TYPES (clé de stabilité)
    # ======================================================
    df["groupe_charges"] = df["groupe_charges"].astype(str)
    df["libelle_groupe"] = df["libelle_groupe"].fillna("")
    df["fournisseur"] = df["fournisseur"].fillna("")

    # ======================================================
    # ÉCRAN 1 — DÉPENSES PAR GROUPE
    # ======================================================
    st.subheader("📊 Dépenses par groupe de charges")

    df_group = (
        df
        .groupby(["groupe_charges", "libelle_groupe"], as_index=False)
        .agg(total_depenses=("montant_ttc", "sum"))
    )

    st.dataframe(
        df_group.rename(columns={
            "groupe_charges": "Groupe",
            "libelle_groupe": "Libellé groupe",
            "total_depenses": "Total dépenses (€)"
        }),
        use_container_width=True
    )

    st.metric(
        "💰 Total général",
        f"{df_group['total_depenses'].sum():,.2f} €"
    )

    # ======================================================
    # ÉCRAN 2 — FILTRES
    # ======================================================
    st.divider()
    st.subheader("🔎 Filtres")

    groupes = ["Tous"] + sorted(df["groupe_charges"].unique().tolist())
    fournisseurs = ["Tous"] + sorted(df["fournisseur"].unique().tolist())

    col1, col2 = st.columns(2)
    groupe_sel = col1.selectbox("Groupe de charges", groupes)
    fournisseur_sel = col2.selectbox("Fournisseur", fournisseurs)

    df_filt = df.copy()

    if groupe_sel != "Tous":
        df_filt = df_filt[df_filt["groupe_charges"] == groupe_sel]

    if fournisseur_sel != "Tous":
        df_filt = df_filt[df_filt["fournisseur"] == fournisseur_sel]

    # ======================================================
    # ÉCRAN 3 — DÉTAIL
    # ======================================================
    st.subheader("📋 Détail des dépenses")

    st.dataframe(
        df_filt[[
            "date",
            "fournisseur",
            "montant_ttc",
            "compte",
            "libelle_compte",
            "groupe_charges",
            "libelle_groupe"
        ]].rename(columns={
            "date": "Date",
            "fournisseur": "Fournisseur",
            "montant_ttc": "Montant (€)",
            "compte": "Compte",
            "libelle_compte": "Libellé compte",
            "groupe_charges": "Groupe",
            "libelle_groupe": "Libellé groupe"
        }),
        use_container_width=True
    )