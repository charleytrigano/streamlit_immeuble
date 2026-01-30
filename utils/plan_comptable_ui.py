import streamlit as st
import pandas as pd
import numpy as np

# =========================
# PLAN COMPTABLE UI
# =========================
def plan_comptable_ui(supabase):

    st.header("📘 Plan comptable – Groupes de charges")

    # =========================
    # CHARGEMENT
    # =========================
    res = (
        supabase
        .table("plan_comptable")
        .select("*")
        .order("groupe_compte")
        .order("compte_8")
        .execute()
    )

    if not res.data:
        st.info("Plan comptable vide")
        return

    df = pd.DataFrame(res.data)

    # Sécurité colonnes
    for col in ["libelle", "libelle_groupe", "groupe_charges"]:
        if col not in df.columns:
            df[col] = None

    # =========================
    # TABLE LECTURE
    # =========================
    st.dataframe(
        df[[
            "compte_8",
            "libelle",
            "groupe_compte",
            "libelle_groupe",
            "groupe_charges"
        ]],
        use_container_width=True,
        hide_index=True
    )

    st.divider()

    # =========================
    # AJOUT
    # =========================
    with st.expander("➕ Ajouter un compte"):
        with st.form("add_compte_form"):
            c1, c2, c3 = st.columns(3)

            compte_8 = c1.text_input("Compte (8 chiffres)")
            libelle = c2.text_input("Libellé")
            groupe_compte = c3.text_input("Groupe comptable (ex : 601)")

            c4, c5 = st.columns(2)
            libelle_groupe = c4.text_input("Libellé groupe")

            groupe_charges = c5.selectbox(
                "Groupe de charges",
                [1, 2, 3, 4, 5],
                format_func=lambda x: {
                    1: "1 – Charges communes générales",
                    2: "2 – Charges RDC / sous-sols",
                    3: "3 – Charges sous-sols",
                    4: "4 – Ascenseurs",
                    5: "5 – Monte-voitures"
                }[x]
            )

            submit_add = st.form_submit_button("➕ Ajouter")

        if submit_add:
            supabase.table("plan_comptable").insert({
                "compte_8": compte_8,
                "libelle": libelle,
                "groupe_compte": groupe_compte,
                "libelle_groupe": libelle_groupe,
                "groupe_charges": groupe_charges
            }).execute()

            st.success("Compte ajouté")
            st.rerun()

    st.divider()

    # =========================
    # MODIFIER / SUPPRIMER
    # =========================
    st.markdown("### ✏️ Modifier / 🗑️ Supprimer")

    selected = st.selectbox(
        "Compte",
        df["compte_8"].tolist()
    )

    row = df[df["compte_8"] == selected].iloc[0]

    # Sécurisation NaN
    gc = row["groupe_charges"]
    if pd.isna(gc):
        gc = 1

    with st.form(f"edit_form_{selected}"):
        c1, c2, c3 = st.columns(3)

        e_libelle = c1.text_input("Libellé", row["libelle"])
        e_groupe_compte = c2.text_input("Groupe comptable", row["groupe_compte"])
        e_libelle_groupe = c3.text_input("Libellé groupe", row["libelle_groupe"])

        e_groupe_charges = st.selectbox(
            "Groupe de charges",
            [1, 2, 3, 4, 5],
            index=[1, 2, 3, 4, 5].index(int(gc)),
            format_func=lambda x: {
                1: "1 – Charges communes générales",
                2: "2 – Charges RDC / sous-sols",
                3: "3 – Charges sous-sols",
                4: "4 – Ascenseurs",
                5: "5 – Monte-voitures"
            }[x]
        )

        col_a, col_b = st.columns(2)
        submit_edit = col_a.form_submit_button("💾 Enregistrer")
        submit_delete = col_b.form_submit_button("🗑️ Supprimer")

    if submit_edit:
        supabase.table("plan_comptable").update({
            "libelle": e_libelle,
            "groupe_compte": e_groupe_compte,
            "libelle_groupe": e_libelle_groupe,
            "groupe_charges": e_groupe_charges
        }).eq("compte_8", selected).execute()

        st.success("Compte mis à jour")
        st.rerun()

    if submit_delete:
        supabase.table("plan_comptable").delete().eq(
            "compte_8", selected
        ).execute()

        st.warning("Compte supprimé")
        st.rerun()