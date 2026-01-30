import streamlit as st
import pandas as pd

GROUPES_CHARGES = {
    1: "Charges communes générales",
    2: "Charges spéciales RDC / sous-sols",
    3: "Charges spéciales sous-sols",
    4: "Ascenseurs",
    5: "Monte-voitures",
}


def plan_comptable_ui(supabase):
    st.header("📘 Plan comptable")

    # =========================
    # LOAD
    # =========================
    res = supabase.table("plan_comptable").select("*").execute()
    if not res.data:
        st.warning("Plan comptable vide")
        return

    df = pd.DataFrame(res.data)

    # Sécurité absolue
    if "groupe_charge" not in df.columns:
        df["groupe_charge"] = None

    df["compte_8"] = df["compte_8"].astype(str)
    df["groupe_charge"] = pd.to_numeric(df["groupe_charge"], errors="coerce")

    # =========================
    # TABLEAU
    # =========================
    st.subheader("📋 Comptes")

    df_display = df.copy()
    df_display["groupe_charge_libelle"] = df_display["groupe_charge"].map(GROUPES_CHARGES)

    selected_index = st.selectbox(
        "Sélectionner un compte",
        options=df_display.index,
        format_func=lambda i: f"{df_display.loc[i,'compte_8']} — {df_display.loc[i,'libelle']}"
    )

    row = df_display.loc[selected_index]

    st.divider()
    st.subheader("✏️ Groupe de charges")

    with st.form("edit_groupe_charge"):
        st.text_input("Compte", row["compte_8"], disabled=True)
        st.text_input("Libellé", row.get("libelle", ""), disabled=True)
        st.text_input("Groupe comptable", row.get("groupe_compte", ""), disabled=True)

        current = row["groupe_charge"]
        keys = list(GROUPES_CHARGES.keys())

        index = keys.index(int(current)) if pd.notna(current) and int(current) in keys else 0

        new_gc = st.selectbox(
            "Groupe de charges",
            options=keys,
            format_func=lambda x: GROUPES_CHARGES[x],
            index=index
        )

        if st.form_submit_button("💾 Enregistrer"):
            supabase.table("plan_comptable").update(
                {"groupe_charge": int(new_gc)}
            ).eq("compte_8", row["compte_8"]).execute()

            st.success("✅ Groupe de charges mis à jour")
            st.rerun()