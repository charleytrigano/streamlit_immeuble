import streamlit as st
import pandas as pd


def plan_comptable_ui(supabase):
    st.title("📘 Plan comptable")

    # =========================
    # CHARGEMENT
    # =========================
    resp = (
        supabase
        .table("plan_comptable")
        .select("id, groupe_compte, libelle_groupe, compte_8, libelle_compte")
        .order("groupe_compte")
        .order("compte_8")
        .execute()
    )

    df = pd.DataFrame(resp.data)

    if df.empty:
        st.warning("Aucun compte dans le plan comptable.")
        return

    # Nettoyage lignes vides
    df = df[
        df["groupe_compte"].notna() &
        (df["groupe_compte"] != "000")
    ]

    # =========================
    # TABS
    # =========================
    tab1, tab2, tab3 = st.tabs(["📋 Consulter", "➕ Ajouter", "✏️ Modifier / 🗑 Supprimer"])

    # =========================
    # CONSULTER
    # =========================
    with tab1:
        st.dataframe(
            df.sort_values(["groupe_compte", "compte_8"]),
            use_container_width=True
        )

    # =========================
    # AJOUTER
    # =========================
    with tab2:
        st.subheader("Ajouter un compte")

        groupe = st.text_input("Groupe de compte (ex: 601)")
        lib_groupe = st.text_input("Libellé du groupe")
        compte_8 = st.text_input("Compte 8 chiffres (ex: 60100100)")
        lib_compte = st.text_input("Libellé du compte")

        if st.button("Ajouter"):
            if not groupe or not compte_8:
                st.error("Groupe et compte sont obligatoires")
            else:
                supabase.table("plan_comptable").insert({
                    "groupe_compte": groupe,
                    "libelle_groupe": lib_groupe,
                    "compte_8": compte_8,
                    "libelle_compte": lib_compte
                }).execute()

                st.success("Compte ajouté")
                st.rerun()

    # =========================
    # MODIFIER / SUPPRIMER
    # =========================
    with tab3:
        st.subheader("Modifier ou supprimer un compte")

        choix = st.selectbox(
            "Sélectionner un compte",
            df["id"],
            format_func=lambda x: (
                df.loc[df["id"] == x, "compte_8"].values[0]
                + " – "
                + df.loc[df["id"] == x, "libelle_compte"].values[0]
            )
        )

        ligne = df[df["id"] == choix].iloc[0]

        new_groupe = st.text_input("Groupe de compte", ligne["groupe_compte"])
        new_lib_groupe = st.text_input("Libellé du groupe", ligne["libelle_groupe"])
        new_compte = st.text_input("Compte 8 chiffres", ligne["compte_8"])
        new_lib = st.text_input("Libellé du compte", ligne["libelle_compte"])

        col1, col2 = st.columns(2)

        with col1:
            if st.button("💾 Modifier"):
                supabase.table("plan_comptable").update({
                    "groupe_compte": new_groupe,
                    "libelle_groupe": new_lib_groupe,
                    "compte_8": new_compte,
                    "libelle_compte": new_lib
                }).eq("id", choix).execute()

                st.success("Compte modifié")
                st.rerun()

        with col2:
            if st.button("🗑 Supprimer"):
                supabase.table("plan_comptable").delete().eq("id", choix).execute()
                st.success("Compte supprimé")
                st.rerun()