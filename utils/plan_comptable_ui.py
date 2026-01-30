import streamlit as st
import pandas as pd

# =========================
# GROUPES DE CHARGES
# =========================
GROUPES_CHARGES = {
    1: "Charges communes générales",
    2: "Charges spéciales RDC / sous-sols",
    3: "Charges spéciales sous-sols",
    4: "Ascenseurs",
    5: "Monte-voitures",
}

# =========================
# UI
# =========================
def plan_comptable_ui(supabase):
    st.header("📘 Plan comptable")

    # =========================
    # LOAD DATA
    # =========================
    res = supabase.table("plan_comptable").select("*").execute()

    if not res.data:
        st.warning("Aucune donnée dans le plan comptable")
        return

    df = pd.DataFrame(res.data)

    # =========================
    # SÉCURITÉ ABSOLUE
    # =========================
    REQUIRED_COLS = [
        "compte_8",
        "libelle",
        "groupe_compte",
        "libelle_groupe",
        "groupe_charge",
    ]

    for col in REQUIRED_COLS:
        if col not in df.columns:
            df[col] = None

    df["compte_8"] = df["compte_8"].astype(str)
    df["groupe_charge"] = pd.to_numeric(df["groupe_charge"], errors="coerce")

    # =========================
    # AFFICHAGE TABLE
    # =========================
    st.subheader("📋 Comptes existants")

    df_view = df.copy()
    df_view["groupe_charge_libelle"] = df_view["groupe_charge"].map(GROUPES_CHARGES)

    st.dataframe(
        df_view[[
            "compte_8",
            "libelle",
            "groupe_compte",
            "libelle_groupe",
            "groupe_charge",
            "groupe_charge_libelle",
        ]].sort_values(["groupe_compte", "compte_8"]),
        use_container_width=True
    )

    st.divider()

    # =========================
    # ÉDITION
    # =========================
    st.subheader("✏️ Modifier le groupe de charges")

    comptes = df["compte_8"].tolist()

    selected_compte = st.selectbox(
        "Compte",
        comptes,
        format_func=lambda c: f"{c} — {df.loc[df['compte_8']==c,'libelle'].values[0]}"
    )

    row = df[df["compte_8"] == selected_compte].iloc[0]

    with st.form("edit_groupe_charge"):
        st.text_input("Libellé", row["libelle"], disabled=True)
        st.text_input("Groupe comptable", row["groupe_compte"], disabled=True)

        current_gc = row["groupe_charge"]
        keys = list(GROUPES_CHARGES.keys())

        index = keys.index(int(current_gc)) if pd.notna(current_gc) and int(current_gc) in keys else 0

        new_gc = st.selectbox(
            "Groupe de charges",
            options=keys,
            format_func=lambda x: GROUPES_CHARGES[x],
            index=index
        )

        submitted = st.form_submit_button("💾 Enregistrer")

        if submitted:
            supabase.table("plan_comptable").update(
                {"groupe_charge": int(new_gc)}
            ).eq("compte_8", selected_compte).execute()

            st.success("✅ Groupe de charges mis à jour")
            st.rerun()