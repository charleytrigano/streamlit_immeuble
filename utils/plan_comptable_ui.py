import streamlit as st
import pandas as pd


def plan_comptable_ui(supabase):

    st.header("📘 Plan comptable")

    # =========================
    # CHARGEMENT
    # =========================
    resp = supabase.table("plan_comptable").select("*").execute()
    df = pd.DataFrame(resp.data)

    if df.empty:
        st.warning("Plan comptable vide")
        return

    # =========================
    # NETTOYAGE AUTOMATIQUE
    # =========================
    df = df[
        df["compte_8"].notna() &
        df["groupe_compte"].notna() &
        (df["libelle_groupe"].fillna("") != "000")
    ]

    # =========================
    # TABLEAU
    # =========================
    st.subheader("📋 Comptes existants")

    st.dataframe(
        df.sort_values(["groupe_compte", "compte_8"]),
        use_container_width=True
    )

    # =========================
    # AJOUT
    # =========================
    st.subheader("➕ Ajouter un compte")

    with st.form("add_compte"):
        c1, c2 = st.columns(2)

        with c1:
            compte_8 = st.text_input("Compte (8 chiffres)")
            groupe_compte = st.text_input("Groupe (3 chiffres)")

        with c2:
            libelle = st.text_input("Libellé compte")
            libelle_groupe = st.text_input("Libellé groupe")

        submit = st.form_submit_button("Ajouter")

        if submit:
            supabase.table("plan_comptable").insert({
                "compte_8": compte_8,
                "libelle": libelle,
                "groupe_compte": groupe_compte,
                "libelle_groupe": libelle_groupe,
            }).execute()

            st.success("Compte ajouté")
            st.rerun()

    # =========================
    # MODIFICATION
    # =========================
    st.subheader("✏️ Modifier un compte")

    compte_sel = st.selectbox(
        "Compte à modifier",
        df["compte_8"].tolist()
    )

    ligne = df[df["compte_8"] == compte_sel].iloc[0]

    with st.form("edit_compte"):
        libelle_new = st.text_input("Libellé compte", ligne["libelle"])
        libelle_groupe_new = st.text_input("Libellé groupe", ligne["libelle_groupe"])

        submit_edit = st.form_submit_button("Modifier")

        if submit_edit:
            supabase.table("plan_comptable").update({
                "libelle": libelle_new,
                "libelle_groupe": libelle_groupe_new,
            }).eq("compte_8", compte_sel).execute()

            st.success("Compte modifié")
            st.rerun()

    # =========================
    # SUPPRESSION
    # =========================
    st.subheader("🗑 Supprimer un compte")

    compte_del = st.selectbox(
        "Compte à supprimer",
        df["compte_8"].tolist(),
        key="delete_compte"
    )

    if st.button("Supprimer définitivement"):
        supabase.table("plan_comptable").delete().eq("compte_8", compte_del).execute()
        st.success("Compte supprimé")
        st.rerun()