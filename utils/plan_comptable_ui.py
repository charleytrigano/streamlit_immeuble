import streamlit as st
import pandas as pd

# =========================
# PLAN COMPTABLE UI
# =========================
def plan_comptable_ui(supabase):

    st.header("📘 Plan comptable")

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
    # FILTRES
    # =========================
    with st.expander("🔎 Filtres", expanded=True):
        col1, col2, col3 = st.columns(3)

        groupe_f = col1.selectbox(
            "Groupe comptable",
            ["Tous"] + sorted(df["groupe_compte"].dropna().unique().tolist())
        )

        charge_f = col2.selectbox(
            "Groupe de charges",
            ["Tous"] + sorted(df["groupe_charges"].dropna().astype(str).unique().tolist())
        )

        libelle_f = col3.text_input("Recherche libellé")

    df_f = df.copy()

    if groupe_f != "Tous":
        df_f = df_f[df_f["groupe_compte"] == groupe_f]

    if charge_f != "Tous":
        df_f = df_f[df_f["groupe_charges"].astype(str) == charge_f]

    if libelle_f:
        df_f = df_f[df_f["libelle"].str.contains(libelle_f, case=False, na=False)]

    # =========================
    # TABLE
    # =========================
    st.markdown("### 📋 Comptes existants")

    st.dataframe(
        df_f.sort_values(["groupe_compte", "compte_8"]),
        use_container_width=True,
        hide_index=True
    )

    st.divider()

    # =========================
    # AJOUT COMPTE
    # =========================
    with st.expander("➕ Ajouter un compte"):
        with st.form("add_compte"):
            col1, col2, col3 = st.columns(3)

            a_compte = col1.text_input("Compte (8 chiffres)")
            a_libelle = col2.text_input("Libellé")
            a_groupe = col3.text_input("Groupe comptable (ex: 601)")

            col4, col5 = st.columns(2)
            a_libelle_grp = col4.text_input("Libellé groupe")
            a_groupe_charges = col5.selectbox(
                "Groupe de charges",
                [
                    1, 2, 3, 4, 5
                ],
                format_func=lambda x: {
                    1: "1 – Charges communes générales",
                    2: "2 – Charges RDC / sous-sols",
                    3: "3 – Charges sous-sols",
                    4: "4 – Ascenseurs",
                    5: "5 – Monte-voitures"
                }[x]
            )

            if st.form_submit_button("➕ Ajouter"):
                supabase.table("plan_comptable").insert({
                    "compte_8": a_compte,
                    "libelle": a_libelle,
                    "groupe_compte": a_groupe,
                    "libelle_groupe": a_libelle_grp,
                    "groupe_charges": a_groupe_charges
                }).execute()

                st.success("Compte ajouté")
                st.rerun()

    st.divider()

    # =========================
    # MODIFIER / SUPPRIMER
    # =========================
    st.markdown("### ✏️ Modifier / 🗑️ Supprimer un compte")

    selected = st.selectbox(
        "Compte à modifier",
        df_f["compte_8"].tolist()
    )

    row = df[df["compte_8"] == selected].iloc[0]

    with st.form(f"edit_{selected}"):
        col1, col2, col3 = st.columns(3)

        e_libelle = col1.text_input("Libellé", row["libelle"])
        e_groupe = col2.text_input("Groupe comptable", row["groupe_compte"])
        e_libelle_grp = col3.text_input("Libellé groupe", row["libelle_groupe"])

        e_groupe_charges = st.selectbox(
            "Groupe de charges",
            [1, 2, 3, 4, 5],
            index=[1, 2, 3, 4, 5].index(int(row["groupe_charges"])) if row["groupe_charges"] else 0,
            format_func=lambda x: {
                1: "1 – Charges communes générales",
                2: "2 – Charges RDC / sous-sols",
                3: "3 – Charges sous-sols",
                4: "4 – Ascenseurs",
                5: "5 – Monte-voitures"
            }[x]
        )

        col_btn1, col_btn2 = st.columns(2)

        if col_btn1.form_submit_button("💾 Enregistrer"):
            supabase.table("plan_comptable").update({
                "libelle": e_libelle,
                "groupe_compte": e_groupe,
                "libelle_groupe": e_libelle_grp,
                "groupe_charges": e_groupe_charges
            }).eq("compte_8", selected).execute()

            st.success("Compte mis à jour")
            st.rerun()

        if col_btn2.form_submit_button("🗑️ Supprimer"):
            supabase.table("plan_comptable").delete().eq(
                "compte_8", selected
            ).execute()

            st.warning("Compte supprimé")
            st.rerun()