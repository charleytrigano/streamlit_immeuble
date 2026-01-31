import streamlit as st
import pandas as pd


def budget_ui(supabase, annee):
    st.subheader(f"💰 Budget – {annee}")

    # =========================
    # Chargement budgets
    # =========================
    res = (
        supabase
        .table("budgets")
        .select("id, annee, groupe_compte, libelle_groupe, budget")
        .eq("annee", annee)
        .execute()
    )

    if res.data:
        df = pd.DataFrame(res.data)
    else:
        df = pd.DataFrame(
            columns=["id", "annee", "groupe_compte", "libelle_groupe", "budget"]
        )

    # =========================
    # FILTRE GROUPE DE COMPTE
    # =========================
    groupes = ["Tous"] + sorted(df["groupe_compte"].dropna().unique().tolist())

    groupe_sel = st.selectbox(
        "Filtrer par groupe de compte",
        groupes,
        key="budget_groupe_compte"
    )

    if groupe_sel != "Tous":
        df_filtre = df[df["groupe_compte"] == groupe_sel]
    else:
        df_filtre = df.copy()

    # =========================
    # KPI
    # =========================
    total_budget = df_filtre["budget"].sum() if not df_filtre.empty else 0

    st.metric("Budget total (filtré)", f"{total_budget:,.2f} €")

    # =========================
    # TABLEAU
    # =========================
    st.markdown("### 📋 Lignes de budget")

    st.dataframe(
        df_filtre.sort_values("groupe_compte"),
        use_container_width=True
    )

    # =========================
    # AJOUT
    # =========================
    with st.expander("➕ Ajouter une ligne de budget"):
        col1, col2 = st.columns(2)

        with col1:
            new_groupe_compte = st.text_input("Groupe de compte")
            new_libelle = st.text_input("Libellé groupe")

        with col2:
            new_budget = st.number_input(
                "Montant du budget",
                min_value=0.0,
                step=100.0
            )

        if st.button("Ajouter", key="budget_add"):
            supabase.table("budgets").insert({
                "annee": annee,
                "groupe_compte": new_groupe_compte,
                "libelle_groupe": new_libelle,
                "budget": new_budget
            }).execute()

            st.success("Ligne de budget ajoutée")
            st.rerun()

    # =========================
    # MODIFIER / SUPPRIMER
    # =========================
    st.markdown("### ✏️ Modifier / Supprimer")

    for _, row in df_filtre.iterrows():
        with st.expander(f"{row['groupe_compte']} – {row['libelle_groupe']}"):
            new_value = st.number_input(
                "Budget",
                value=float(row["budget"]),
                min_value=0.0,
                step=100.0,
                key=f"edit_budget_{row['id']}"
            )

            col1, col2 = st.columns(2)

            with col1:
                if st.button("💾 Enregistrer", key=f"save_{row['id']}"):
                    supabase.table("budgets").update({
                        "budget": new_value
                    }).eq("id", row["id"]).execute()

                    st.success("Budget mis à jour")
                    st.rerun()

            with col2:
                if st.button("🗑️ Supprimer", key=f"delete_{row['id']}"):
                    supabase.table("budgets").delete().eq(
                        "id", row["id"]
                    ).execute()

                    st.warning("Ligne supprimée")
                    st.rerun()