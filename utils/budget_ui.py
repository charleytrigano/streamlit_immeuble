import streamlit as st
import pandas as pd


# ======================================================
# BUDGET UI
# ======================================================
def budget_ui(supabase):

    tabs = st.tabs(
        ["📊 Consulter", "➕ Ajouter", "✏️ Modifier", "🗑 Supprimer"]
    )

    # ======================================================
    # 📊 CONSULTER
    # ======================================================
    with tabs[0]:
        st.subheader("📊 Budget – Consultation")

        data = supabase.table("budgets").select("*").execute().data
        df = pd.DataFrame(data)

        if df.empty:
            st.info("Aucun budget enregistré.")
            return

        # ---- Filtres ----
        col1, col2 = st.columns(2)

        with col1:
            annee = st.selectbox(
                "Année",
                ["Toutes"] + sorted(df["annee"].unique().tolist())
            )

        with col2:
            compte = st.selectbox(
                "Compte",
                ["Tous"] + sorted(df["compte"].unique().tolist())
            )

        if annee != "Toutes":
            df = df[df["annee"] == annee]

        if compte != "Tous":
            df = df[df["compte"] == compte]

        # ---- KPIs ----
        c1, c2, c3 = st.columns(3)
        c1.metric("Budget total (€)", f"{df['budget'].sum():,.2f}")
        c2.metric("Nombre de comptes", df["compte"].nunique())
        c3.metric("Budget moyen (€)", f"{df['budget'].mean():,.2f}")

        # ---- Tableau ----
        st.dataframe(
            df.sort_values(["annee", "compte"]),
            use_container_width=True
        )

    # ======================================================
    # ➕ AJOUTER (UPSERT)
    # ======================================================
    with tabs[1]:
        st.subheader("➕ Ajouter / Remplacer un budget")

        with st.form("add_budget"):
            annee = st.number_input("Année", value=2025)
            compte = st.text_input("Compte (ex: 606, 6221)")
            budget = st.number_input("Budget (€)", step=100.0)
            groupe = st.text_input("Groupe de compte (optionnel)")

            submitted = st.form_submit_button("Enregistrer")

        if submitted:
            supabase.table("budgets").upsert(
                {
                    "annee": int(annee),
                    "compte": compte,
                    "budget": float(budget),
                    "groupe_compte": groupe,
                },
                on_conflict="annee,compte"
            ).execute()

            st.success("Budget enregistré (ajout ou mise à jour).")

    # ======================================================
    # ✏️ MODIFIER
    # ======================================================
    with tabs[2]:
        st.subheader("✏️ Modifier un budget existant")

        data = supabase.table("budgets").select("*").execute().data
        df = pd.DataFrame(data)

        if df.empty:
            st.info("Aucun budget à modifier.")
            return

        bud_id = st.selectbox(
            "Sélectionner un budget",
            df["id"],
            format_func=lambda x: (
                f"{df.loc[df['id']==x,'annee'].values[0]} – "
                f"{df.loc[df['id']==x,'compte'].values[0]}"
            )
        )

        row = df[df["id"] == bud_id].iloc[0]

        new_budget = st.number_input(
            "Nouveau budget (€)",
            value=float(row["budget"])
        )

        if st.button("Mettre à jour"):
            supabase.table("budgets") \
                .update({"budget": float(new_budget)}) \
                .eq("id", bud_id) \
                .execute()

            st.success("Budget mis à jour.")

    # ======================================================
    # 🗑 SUPPRIMER
    # ======================================================
    with tabs[3]:
        st.subheader("🗑 Supprimer un budget")

        data = supabase.table("budgets").select("*").execute().data
        df = pd.DataFrame(data)

        if df.empty:
            st.info("Aucun budget à supprimer.")
            return

        bud_id = st.selectbox(
            "Budget à supprimer",
            df["id"],
            format_func=lambda x: (
                f"{df.loc[df['id']==x,'annee'].values[0]} – "
                f"{df.loc[df['id']==x,'compte'].values[0]}"
            )
        )

        if st.button("Supprimer définitivement"):
            supabase.table("budgets") \
                .delete() \
                .eq("id", bud_id) \
                .execute()

            st.success("Budget supprimé.")
