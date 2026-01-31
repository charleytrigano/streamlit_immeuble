import streamlit as st
import pandas as pd
from datetime import date


def depenses_ui(supabase, annee):
    st.header(f"📄 Dépenses – {annee}")

    # ======================================================
    # SOUS-ONGLETS
    # ======================================================
    tab_detail, tab_groupes = st.tabs([
        "📋 Détail des dépenses",
        "📊 Dépenses par groupes de charges"
    ])

    # ======================================================
    # ONGLET 1 — DÉTAIL DES DÉPENSES (FIGÉ)
    # ======================================================
    with tab_detail:
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
            .order("date")
            .execute()
        )

        if not resp.data:
            st.info("Aucune dépense pour cette année.")
            return

        df = pd.DataFrame(resp.data)

        # ---------- filtres ----------
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

        # ---------- tableau ----------
        st.subheader("📋 Détail")

        st.dataframe(
            df_f[[
                "date",
                "compte",
                "poste",
                "fournisseur",
                "montant_ttc",
                "lot_id",
                "commentaire"
            ]],
            use_container_width=True
        )

        # 👉 ici : ton Ajouter / Modifier / Supprimer
        # (volontairement inchangé)

    # ======================================================
    # ONGLET 2 — DÉPENSES PAR GROUPES DE CHARGES
    # ======================================================
    with tab_groupes:
        st.subheader("📊 Dépenses par groupes de charges")

        resp = (
            supabase
            .table("v_depenses_enrichies")
            .select("""
                annee,
                groupe_charges,
                montant_ttc
            """)
            .eq("annee", annee)
            .execute()
        )

        if not resp.data:
            st.info("Aucune donnée pour cette année.")
            return

        df = pd.DataFrame(resp.data)

        # ---------- agrégation ----------
        df_group = (
            df
            .groupby("groupe_charges", as_index=False)
            .agg(
                total_depenses=("montant_ttc", "sum"),
                nb_depenses=("montant_ttc", "count")
            )
            .sort_values("groupe_charges")
        )

        df_group["total_depenses"] = df_group["total_depenses"].round(2)

        # ---------- KPI ----------
        col1, col2 = st.columns(2)
        col1.metric(
            "Total des dépenses",
            f"{df_group['total_depenses'].sum():,.2f} €".replace(",", " ")
        )
        col2.metric(
            "Nombre de lignes",
            int(df_group["nb_depenses"].sum())
        )

        # ---------- tableau ----------
        st.dataframe(
            df_group.rename(columns={
                "groupe_charges": "Groupe de charges",
                "total_depenses": "Total (€)",
                "nb_depenses": "Nombre de dépenses"
            }),
            use_container_width=True
        )