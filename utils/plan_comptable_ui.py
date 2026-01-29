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
    # CHARGEMENT
    # =========================
    res = supabase.table("plan_comptable").select("*").execute()
    if not res.data:
        st.warning("Aucun compte dans le plan comptable.")
        return

    df = pd.DataFrame(res.data)

    # Nettoyage
    df["compte_8"] = df["compte_8"].astype(str)
    df["groupe_charge"] = pd.to_numeric(df["groupe_charge"], errors="coerce")

    # =========================
    # AFFICHAGE TABLE
    # =========================
    st.subheader("📋 Comptes")

    for _, row in df.sort_values(["groupe_compte", "compte_8"]).iterrows():
        with st.expander(f"{row['compte_8']} — {row.get('libelle', '')}", expanded=False):
            col1, col2 = st.columns(2)

            with col1:
                st.text_input(
                    "Compte",
                    value=row["compte_8"],
                    disabled=True
                )

                st.text_input(
                    "Libellé",
                    value=row.get("libelle", ""),
                    disabled=True
                )

                st.text_input(
                    "Groupe comptable",
                    value=row.get("groupe_compte", ""),
                    disabled=True
                )

            with col2:
                current_gc = row.get("groupe_charge")
                current_index = (
                    list(GROUPES_CHARGES.keys()).index(current_gc)
                    if current_gc in GROUPES_CHARGES
                    else 0
                )

                new_gc = st.selectbox(
                    "Groupe de charges",
                    options=list(GROUPES_CHARGES.keys()),
                    format_func=lambda x: GROUPES_CHARGES[x],
                    index=current_index,
                    key=f"gc_{row['compte_8']}"
                )

                if st.button("💾 Enregistrer", key=f"save_{row['compte_8']}"):
                    supabase.table("plan_comptable").update(
                        {"groupe_charge": new_gc}
                    ).eq("compte_8", row["compte_8"]).execute()

                    st.success("Groupe de charges mis à jour")