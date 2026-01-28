import streamlit as st
import pandas as pd


def plan_comptable_ui(supabase):
    st.header("📚 Plan comptable")

    res = (
        supabase
        .table("plan_comptable")
        .select("*")
        .order("groupe_compte")
        .order("compte_8")
        .execute()
    )

    df = pd.DataFrame(res.data or [])

    st.dataframe(
        df.sort_values(["groupe_compte", "compte_8"]),
        use_container_width=True
    )

    st.subheader("➕ Ajouter / modifier un compte")

    with st.form("plan_form"):
        compte_8 = st.text_input("Compte (8 chiffres)")
        libelle = st.text_input("Libellé")
        groupe = st.text_input("Groupe (ex: 601)")
        libelle_groupe = st.text_input("Libellé groupe")

        action = st.selectbox("Action", ["Ajouter", "Modifier", "Supprimer"])
        submit = st.form_submit_button("Valider")

        if submit:
            if action == "Ajouter":
                supabase.table("plan_comptable").insert({
                    "compte_8": compte_8,
                    "libelle": libelle,
                    "groupe_compte": groupe,
                    "libelle_groupe": libelle_groupe
                }).execute()

            elif action == "Modifier":
                supabase.table("plan_comptable").update({
                    "libelle": libelle,
                    "groupe_compte": groupe,
                    "libelle_groupe": libelle_groupe
                }).eq("compte_8", compte_8).execute()

            elif action == "Supprimer":
                supabase.table("plan_comptable").delete().eq(
                    "compte_8", compte_8
                ).execute()

            st.success("Action effectuée")
            st.experimental_rerun()