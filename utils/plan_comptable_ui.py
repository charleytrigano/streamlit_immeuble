import streamlit as st
import pandas as pd

GROUPES_CHARGES = {
    1: "Charges communes générales",
    2: "Charges communes RDC / sous-sols",
    3: "Charges spéciales sous-sols",
    4: "Charges garages / parkings",
    5: "Ascenseurs",
    6: "Monte-voitures",
}

def plan_comptable_ui(supabase):
    st.subheader("📘 Plan comptable – Groupes de charges")

    # =========================
    # Chargement des données
    # =========================
    res = (
        supabase
        .table("plan_comptable")
        .select("compte_8, libelle, groupe_charges")
        .order("compte_8")
        .execute()
    )

    if not res.data:
        st.warning("Aucune donnée dans le plan comptable")
        return

    df = pd.DataFrame(res.data)

    # Sécurité absolue
    if "groupe_charges" not in df.columns:
        st.error("❌ Colonne groupe_charges absente en base")
        return

    df["groupe_charges"] = pd.to_numeric(df["groupe_charges"], errors="coerce")

    # =========================
    # Sélection du compte
    # =========================
    comptes = df["compte_8"].tolist()

    selected_compte = st.selectbox(
        "Compte comptable",
        options=comptes,
        format_func=lambda c: f"{c} – {df.loc[df['compte_8']==c, 'libelle'].values[0]}"
    )

    ligne = df[df["compte_8"] == selected_compte].iloc[0]

    # =========================
    # Sélection du groupe
    # =========================
    current_groupe = int(ligne["groupe_charges"]) if pd.notna(ligne["groupe_charges"]) else None

    selected_groupe = st.selectbox(
        "Groupe de charges",
        options=list(GROUPES_CHARGES.keys()),
        index=list(GROUPES_CHARGES.keys()).index(current_groupe)
        if current_groupe in GROUPES_CHARGES else 0,
        format_func=lambda k: f"{k} – {GROUPES_CHARGES[k]}"
    )

    # =========================
    # Sauvegarde
    # =========================
    if st.button("💾 Enregistrer"):
        (
            supabase
            .table("plan_comptable")
            .update({"groupe_charges": selected_groupe})
            .eq("compte_8", selected_compte)
            .execute()
        )

        st.success("✅ Groupe de charges mis à jour")
        st.rerun()

    # =========================
    # Vue globale
    # =========================
    st.markdown("### 📋 Vue complète")

    df["groupe_label"] = df["groupe_charges"].map(GROUPES_CHARGES)

    st.dataframe(
        df[["compte_8", "libelle", "groupe_charges", "groupe_label"]],
        use_container_width=True
    )