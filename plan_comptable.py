import streamlit as st
import pandas as pd
from supabase import create_client

# ======================================================
# 🔐 SUPABASE
# ======================================================
SUPABASE_URL = st.secrets["SUPABASE_URL"]
SUPABASE_KEY = st.secrets["SUPABASE_ANON_KEY"]

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# ======================================================
# 📥 LOAD
# ======================================================
def load_plan():
    data = supabase.table("plan_comptable").select("*").execute().data
    df = pd.DataFrame(data)

    if df.empty:
        return df

    # Nettoyage des lignes parasites
    df = df[
        (df["compte_8"].notna()) &
        (df["compte_8"] != "") &
        (df["libelle"].notna()) &
        (df["libelle"] != "") &
        (df["libelle_groupe"] != "000")
    ]

    return df


# ======================================================
# 📚 UI
# ======================================================
def render():
    st.title("📚 Plan comptable")

    df = load_plan()

    # ==========================
    # 📋 LISTE
    # ==========================
    st.subheader("Liste des comptes")

    if df.empty:
        st.info("Aucun compte")
    else:
        st.dataframe(
            df.sort_values(["groupe_compte", "compte_8"]),
            use_container_width=True
        )

    st.divider()

    # ==========================
    # ➕ AJOUT
    # ==========================
    st.subheader("➕ Ajouter un compte")

    with st.form("add_plan"):
        c1, c2 = st.columns(2)

        with c1:
            compte_8 = st.text_input("Compte (8 chiffres)")
            libelle = st.text_input("Libellé")

        with c2:
            groupe_compte = st.text_input("Groupe de compte (ex : 615)")
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

    st.divider()

    # ==========================
    # ✏️ MODIFICATION
    # ==========================
    st.subheader("✏️ Modifier un compte")

    if not df.empty:
        compte_sel = st.selectbox(
            "Compte",
            df["compte_8"].tolist()
        )

        row = df[df["compte_8"] == compte_sel].iloc[0]

        with st.form("edit_plan"):
            c1, c2 = st.columns(2)

            with c1:
                libelle_edit = st.text_input("Libellé", row["libelle"])
            with c2:
                libelle_groupe_edit = st.text_input(
                    "Libellé groupe",
                    row["libelle_groupe"]
                )

            if st.form_submit_button("Enregistrer"):
                supabase.table("plan_comptable").update({
                    "libelle": libelle_edit,
                    "libelle_groupe": libelle_groupe_edit
                }).eq("compte_8", compte_sel).execute()

                st.success("Compte modifié")
                st.rerun()

    st.divider()

    # ==========================
    # 🗑 SUPPRESSION
    # ==========================
    st.subheader("🗑 Supprimer un compte")

    if not df.empty:
        compte_del = st.selectbox(
            "Compte à supprimer",
            df["compte_8"].tolist(),
            key="delete_plan"
        )

        st.warning("⚠️ Suppression définitive")

        if st.button("Supprimer"):
            supabase.table("plan_comptable").delete().eq(
                "compte_8", compte_del
            ).execute()

            st.success("Compte supprimé")
            st.rerun()