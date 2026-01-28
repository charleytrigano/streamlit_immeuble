import streamlit as st
import pandas as pd

def plan_comptable_ui(supabase):
    st.title("📚 Plan comptable")

    resp = supabase.table("plan_comptable").select("*").execute()
    df = pd.DataFrame(resp.data)

    if df.empty:
        st.warning("Plan comptable vide")
        return

    df = df[
        (df["groupe_compte"] != "000") &
        df["compte_8"].notna()
    ]

    st.subheader("📋 Liste des comptes")
    st.dataframe(
        df.sort_values(["groupe_compte", "compte_8"]),
        use_container_width=True
    )

    # -------------------------
    # MODIFIER LIBELLÉ GROUPE
    # -------------------------
    st.subheader("✏️ Modifier libellé de groupe")

    grp = st.selectbox(
        "Groupe de compte",
        sorted(df["groupe_compte"].unique())
    )

    current = df[df["groupe_compte"] == grp]["libelle_groupe"].iloc[0]

    new_label = st.text_input(
        "Libellé du groupe",
        value=current
    )

    if st.button("Mettre à jour"):
        supabase.table("plan_comptable") \
            .update({"libelle_groupe": new_label}) \
            .eq("groupe_compte", grp) \
            .execute()
        st.success("Libellé mis à jour")
        st.rerun()

    # -------------------------
    # AJOUT COMPTE
    # -------------------------
    st.subheader("➕ Ajouter un compte")

    with st.form("add_compte"):
        compte_8 = st.text_input("Compte (8 chiffres)")
        libelle = st.text_input("Libellé du compte")
        groupe_compte = st.text_input("Groupe")
        libelle_groupe = st.text_input("Libellé groupe")

        if st.form_submit_button("Ajouter"):
            supabase.table("plan_comptable").insert({
                "compte_8": compte_8,
                "libelle": libelle,
                "groupe_compte": groupe_compte,
                "libelle_groupe": libelle_groupe
            }).execute()
            st.success("Compte ajouté")
            st.rerun()

    # -------------------------
    # SUPPRESSION
    # -------------------------
    st.subheader("🗑 Supprimer un compte")

    compte_del = st.selectbox(
        "Compte à supprimer",
        df["compte_8"]
    )

    if st.button("Supprimer définitivement"):
        supabase.table("plan_comptable") \
            .delete() \
            .eq("compte_8", compte_del) \
            .execute()
        st.success("Compte supprimé")
        st.rerun()