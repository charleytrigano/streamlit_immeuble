import streamlit as st
import pandas as pd


def euro(x):
    try:
        return f"{x:,.2f} €".replace(",", " ").replace(".", ",")
    except Exception:
        return "0,00 €"


def depenses_ui(supabase, annee):
    st.header(f"📄 Dépenses – {annee}")

    # ======================================================
    # LECTURE : vue enrichie
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
        return

    df = pd.DataFrame(resp.data)
    df["montant_ttc"] = pd.to_numeric(df["montant_ttc"], errors="coerce").fillna(0)

    # ======================================================
    # FILTRES
    # ======================================================
    st.subheader("🔎 Filtres")

    col1, col2 = st.columns(2)

    with col1:
        groupes = ["Tous"] + sorted(df["groupe_charges"].dropna().unique().tolist())
        groupe_sel = st.selectbox("Groupe de charges", groupes)

    with col2:
        comptes = ["Tous"] + sorted(df["compte"].dropna().unique().tolist())
        compte_sel = st.selectbox("Compte comptable", comptes)

    df_f = df.copy()

    if groupe_sel != "Tous":
        df_f = df_f[df_f["groupe_charges"] == groupe_sel]

    if compte_sel != "Tous":
        df_f = df_f[df_f["compte"] == compte_sel]

    # ======================================================
    # TABLEAU 1 — DÉPENSES PAR GROUPE DE CHARGES
    # ======================================================
    st.subheader("📊 Dépenses par groupe de charges")

    df_group = (
        df_f
        .groupby("groupe_charges", as_index=False)
        .agg(total_depenses=("montant_ttc", "sum"))
    )

    df_group["total_depenses"] = df_group["total_depenses"].apply(euro)

    st.dataframe(df_group, use_container_width=True)

    # ======================================================
    # TABLEAU 2 — DÉTAIL DES DÉPENSES (LECTURE)
    # ======================================================
    st.subheader("📋 Détail des dépenses")

    st.dataframe(
        df_f[[
            "depense_id",
            "date",
            "compte",
            "poste",
            "montant_ttc",
            "groupe_charges",
            "libelle_compte"
        ]],
        use_container_width=True
    )

    # ======================================================
    # CRUD — ÉDITION DIRECTE TABLE depenses
    # ======================================================
    st.subheader("✏️ Ajouter / Modifier / Supprimer")

    resp_edit = (
        supabase
        .table("depenses")
        .select("id, date, compte, poste, montant_ttc, annee")
        .eq("annee", annee)
        .execute()
    )

    df_edit = pd.DataFrame(resp_edit.data) if resp_edit.data else pd.DataFrame(
        columns=["id", "date", "compte", "poste", "montant_ttc", "annee"]
    )

    edited_df = st.data_editor(
        df_edit,
        use_container_width=True,
        num_rows="dynamic",
        key="depenses_editor"
    )

    if st.button("💾 Enregistrer"):
        for _, row in edited_df.iterrows():
            if pd.isna(row["id"]):
                supabase.table("depenses").insert({
                    "annee": annee,
                    "date": row["date"],
                    "compte": row["compte"],
                    "poste": row["poste"],
                    "montant_ttc": row["montant_ttc"]
                }).execute()
            else:
                supabase.table("depenses").update({
                    "date": row["date"],
                    "compte": row["compte"],
                    "poste": row["poste"],
                    "montant_ttc": row["montant_ttc"]
                }).eq("id", row["id"]).execute()

        st.success("✅ Dépenses enregistrées")
        st.rerun()