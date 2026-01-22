import streamlit as st
import pandas as pd
from datetime import datetime

# -----------------------------
# CONFIG MÉTIER
# -----------------------------
ANNEES_DISPONIBLES = [2023, 2024, 2025, 2026]

# -----------------------------
# DATA ACCESS
# -----------------------------
def load_budgets(supabase, annee: int) -> pd.DataFrame:
    resp = (
        supabase
        .table("budgets")
        .select("*")
        .eq("annee", annee)
        .order("compte")
        .execute()
    )

    data = resp.data or []
    return pd.DataFrame(data)


# -----------------------------
# UI PRINCIPALE
# -----------------------------
def budget_ui(supabase):
    st.title("💰 Budget")
    st.subheader("Pilotage des charges de l’immeuble")

    # -------------------------
    # Sélection année (LIBRE)
    # -------------------------
    annee = st.selectbox(
        "Année budgétaire",
        ANNEES_DISPONIBLES,
        index=ANNEES_DISPONIBLES.index(datetime.now().year)
        if datetime.now().year in ANNEES_DISPONIBLES else 0
    )

    df = load_budgets(supabase, annee)

    # -------------------------
    # KPI (TOUJOURS AFFICHÉS)
    # -------------------------
    total_budget = float(df["budget"].sum()) if not df.empty else 0.0
    nb_comptes = int(df["compte"].nunique()) if not df.empty else 0
    budget_moyen = total_budget / nb_comptes if nb_comptes > 0 else 0.0

    c1, c2, c3 = st.columns(3)
    c1.metric("Budget total (€)", f"{total_budget:,.2f}")
    c2.metric("Nombre de comptes", nb_comptes)
    c3.metric("Budget moyen (€)", f"{budget_moyen:,.2f}")

    st.divider()

    # -------------------------
    # ONGLET CRUD
    # -------------------------
    tab_consulter, tab_ajouter, tab_modifier, tab_supprimer = st.tabs(
        ["📊 Consulter", "➕ Ajouter", "✏️ Modifier", "🗑️ Supprimer"]
    )

    # ==========================================================
    # CONSULTER
    # ==========================================================
    with tab_consulter:
        if df.empty:
            st.info("Aucun budget enregistré pour cette année.")
        else:
            st.dataframe(
                df[["annee", "compte", "budget", "groupe_compte"]],
                use_container_width=True
            )

    # ==========================================================
    # AJOUTER
    # ==========================================================
    with tab_ajouter:
        st.subheader("Ajouter un budget")

        compte = st.text_input("Compte")
        budget = st.number_input("Budget (€)", min_value=0.0, step=50.0)
        groupe = st.text_input("Groupe de compte (optionnel)")

        if st.button("💾 Enregistrer le budget"):
            if not compte:
                st.error("Le compte est obligatoire.")
            else:
                supabase.table("budgets").insert({
                    "annee": annee,
                    "compte": compte,
                    "budget": budget,
                    "groupe_compte": groupe or compte
                }).execute()

                st.success("Budget ajouté avec succès.")
                st.rerun()

    # ==========================================================
    # MODIFIER
    # ==========================================================
    with tab_modifier:
        st.subheader("Modifier un budget")

        if df.empty:
            st.warning("Aucun budget à modifier pour cette année.")
        else:
            selection = st.selectbox(
                "Sélectionner un compte",
                df["compte"].tolist()
            )

            row = df[df["compte"] == selection].iloc[0]

            new_budget = st.number_input(
                "Nouveau budget (€)",
                value=float(row["budget"]),
                min_value=0.0,
                step=50.0
            )

            new_groupe = st.text_input(
                "Groupe de compte",
                value=row.get("groupe_compte", "")
            )

            if st.button("✏️ Mettre à jour"):
                supabase.table("budgets").update({
                    "budget": new_budget,
                    "groupe_compte": new_groupe
                }).eq("id", row["id"]).execute()

                st.success("Budget modifié.")
                st.rerun()

    # ==========================================================
    # SUPPRIMER
    # ==========================================================
    with tab_supprimer:
        st.subheader("Supprimer un budget")

        if df.empty:
            st.warning("Aucun budget à supprimer pour cette année.")
        else:
            selection = st.selectbox(
                "Sélectionner un compte à supprimer",
                df["compte"].tolist()
            )

            row = df[df["compte"] == selection].iloc[0]

            st.error(
                f"Suppression définitive du budget du compte {selection} ({row['budget']} €)"
            )

            if st.button("🗑️ Confirmer la suppression"):
                supabase.table("budgets").delete().eq("id", row["id"]).execute()
                st.success("Budget supprimé.")
                st.rerun()