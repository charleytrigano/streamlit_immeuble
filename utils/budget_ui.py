import streamlit as st
import pandas as pd


def budget_ui(supabase):
    st.header("💰 Budget")

    # =========================
    # CHARGEMENT DONNÉES
    # =========================
    df_all = pd.DataFrame(
        supabase.table("budgets").select("*").execute().data
    )

    # =========================
    # SOUS-ONGLETS
    # =========================
    tab_consult, tab_add, tab_edit, tab_delete = st.tabs(
        ["📊 Consulter", "➕ Ajouter", "✏️ Modifier", "🗑 Supprimer"]
    )

    # ======================================================
    # 📊 CONSULTER
    # ======================================================
    with tab_consult:
        if df_all.empty:
            st.info("Aucun budget enregistré.")
            return

        # ---------- FILTRES ----------
        col1, col2 = st.columns(2)

        with col1:
            annee = st.selectbox(
                "Année",
                sorted(df_all["annee"].unique())
            )

        with col2:
            compte = st.selectbox(
                "Compte",
                ["Tous"] + sorted(df_all["compte"].unique())
            )

        df = df_all[df_all["annee"] == annee]
        if compte != "Tous":
            df = df[df["compte"] == compte]

        # ---------- KPI ----------
        k1, k2 = st.columns(2)
        k1.metric("Budget total (€)", f"{df['budget'].sum():,.0f}")
        k2.metric("Nombre de postes", len(df))

        # ---------- TABLEAU ----------
        st.dataframe(
            df.sort_values("compte"),
            use_container_width=True
        )

    # ======================================================
    # ➕ AJOUTER
    # ======================================================
    with tab_add:
        st.subheader("➕ Ajouter un budget")

        with st.form("add_budget"):
            annee = st.number_input(
                "Année",
                min_value=2000,
                max_value=2100,
                value=2025,
                step=1,
            )
            compte = st.text_input("Compte (ex: 606, 615, 6221)")
            budget = st.number_input(
                "Budget (€)",
                min_value=0.0,
                step=100.0,
            )

            submitted = st.form_submit_button("💾 Enregistrer")

        if submitted:
            if not compte:
                st.error("Le compte est obligatoire.")
            else:
                supabase.table("budgets").upsert(
                    {
                        "annee": int(annee),
                        "compte": compte,
                        "budget": float(budget),
                    },
                    on_conflict="annee,compte",
                ).execute()

                st.success("Budget ajouté / mis à jour.")
                st.rerun()

    # ======================================================
    # ✏️ MODIFIER
    # ======================================================
    with tab_edit:
        st.subheader("✏️ Modifier un budget existant")

        if df_all.empty:
            st.info("Aucun budget à modifier.")
            return

        budget_id = st.selectbox(
            "Sélectionner un poste",
            df_all["id"],
            format_func=lambda i: (
                f"{df_all.loc[df_all['id'] == i, 'annee'].values[0]} – "
                f"{df_all.loc[df_all['id'] == i, 'compte'].values[0]}"
            ),
        )

        row = df_all[df_all["id"] == budget_id].iloc[0]

        new_budget = st.number_input(
            "Nouveau budget (€)",
            value=float(row["budget"]),
            step=100.0,
        )

        if st.button("💾 Enregistrer la modification"):
            supabase.table("budgets") \
                .update({"budget": float(new_budget)}) \
                .eq("id", budget_id) \
                .execute()

            st.success("Budget modifié.")
            st.rerun()

    # ======================================================
    # 🗑 SUPPRIMER
    # ======================================================
    with tab_delete:
        st.subheader("🗑 Supprimer un budget")

        if df_all.empty:
            st.info("Aucun budget à supprimer.")
            return

        budget_id = st.selectbox(
            "Budget à supprimer",
            df_all["id"],
            format_func=lambda i: (
                f"{df_all.loc[df_all['id'] == i, 'annee'].values[0]} – "
                f"{df_all.loc[df_all['id'] == i, 'compte'].values[0]}"
            ),
        )

        st.warning("⚠️ Cette action est définitive.")

        if st.button("❌ Supprimer définitivement"):
            supabase.table("budgets") \
                .delete() \
                .eq("id", budget_id) \
                .execute()

            st.success("Budget supprimé.")
            st.rerun()