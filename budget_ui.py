import streamlit as st
import pandas as pd


def budget_ui(supabase, annee):
    st.subheader(f"💰 Budget – {annee}")

    # =========================
    # Chargement budgets
    # =========================
    bud = (
        supabase
        .table("budgets")
        .select("id, annee, groupe_compte, libelle_groupe, budget")
        .eq("annee", annee)
        .execute()
    )

    if not bud.data:
        df = pd.DataFrame(columns=["id", "annee", "groupe_compte", "libelle_groupe", "budget"])
    else:
        df = pd.DataFrame(bud.data)

    # =========================
    # KPI
    # =========================
    total_budget = df["budget"].sum() if not df.empty else 0
    st.metric("Budget total", f"{total_budget:,.2f} €")

    # =========================
    # Tableau
    # =========================
    st.markdown("### 📋 Lignes de budget")

    st.dataframe(
        df.sort_values("groupe_compte"),
        use_container_width=True
    )

    # =========================
    # AJOUT
    # =========================
    with st.expander("➕ Ajouter une ligne de budget"):
        col1, col2 = st.columns(2)

        with col1:
            groupe_compte = st.text_input("Groupe de compte")
            libelle_groupe = st.text_input("Libellé groupe")

        with col2:
            montant = st.number_input("Budget", min_value=0.0, step=100.0)

        if st.button("Ajouter", key="budget_add"):
            supabase.table("budgets").insert({
                "annee": annee,
                "groupe_compte": groupe_compte,
                "libelle_groupe": libelle_groupe,
                "budget": montant
            }).execute()
            st.success("Ligne ajoutée")
            st.rerun()

    # =========================
    # MODIFIER / SUPPRIMER
    # =========================
    st.markdown("### ✏️ Modifier / Supprimer")

    for _, row in df.iterrows():
        with st.expander(f"{row['groupe_compte']} – {row['libelle_groupe']}"):
            new_budget = st.number_input(
                "Budget",
                value=float(row["budget"]),
                min_value=0.0,
                step=100.0,
                key=f"bud_edit_{row['id']}"
            )

            col1, col2 = st.columns(2)

            with col1:
                if st.button("💾 Enregistrer", key=f"bud_save_{row['id']}"):
                    supabase.table("budgets").update({
                        "budget": new_budget
                    }).eq("id", row["id"]).execute()
                    st.success("Budget mis à jour")
                    st.rerun()

            with col2:
                if st.button("🗑️ Supprimer", key=f"bud_del_{row['id']}"):
                    supabase.table("budgets").delete().eq("id", row["id"]).execute()
                    st.warning("Ligne supprimée")
                    st.rerun()