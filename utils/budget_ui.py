import streamlit as st
import pandas as pd


def budget_ui(supabase):
    st.header("💼 Budget")

    # =========================
    # Chargement des données
    # =========================
    response = supabase.table("budgets").select("*").execute()
    data = response.data or []
    df = pd.DataFrame(data)

    if not df.empty:
        df["annee"] = df["annee"].astype(int)
        df["compte"] = df["compte"].astype(str)
        df["budget"] = df["budget"].astype(float)

    # =========================
    # Sélecteur année global
    # =========================
    annees_dispo = sorted(df["annee"].unique()) if not df.empty else []
    annee_active = st.selectbox(
        "Année budgétaire",
        annees_dispo if annees_dispo else [2025],
    )

    # =========================
    # Sous-onglets
    # =========================
    tab_consulter, tab_ajouter, tab_modifier, tab_supprimer = st.tabs(
        ["📊 Consulter", "➕ Ajouter", "✏️ Modifier", "🗑 Supprimer"]
    )

    # ======================================================
    # 📊 CONSULTER
    # ======================================================
    with tab_consulter:
        if df.empty:
            st.info("Aucun budget enregistré.")
        else:
            df_view = df[df["annee"] == annee_active]

            # ---------- Filtres ----------
            col1, col2 = st.columns(2)
            with col1:
                compte_filtre = st.selectbox(
                    "Compte",
                    ["Tous"] + sorted(df_view["compte"].unique()),
                )
            with col2:
                pass

            if compte_filtre != "Tous":
                df_view = df_view[df_view["compte"] == compte_filtre]

            # ---------- KPI ----------
            k1, k2, k3 = st.columns(3)
            k1.metric("💰 Budget total", f"{df_view['budget'].sum():,.2f} €")
            k2.metric("📂 Nombre de comptes", df_view["compte"].nunique())
            k3.metric("📊 Budget moyen", f"{df_view['budget'].mean():,.2f} €")

            # ---------- Tableau ----------
            st.dataframe(
                df_view.sort_values("compte"),
                use_container_width=True,
            )

    # ======================================================
    # ➕ AJOUTER
    # ======================================================
    with tab_ajouter:
        with st.form("ajout_budget"):
            compte = st.text_input("Compte")
            budget = st.number_input("Budget (€)", min_value=0.0, step=10.0)

            submitted = st.form_submit_button("💾 Enregistrer")

            if submitted:
                if not compte:
                    st.error("Le compte est obligatoire.")
                else:
                    supabase.table("budgets").upsert(
                        {
                            "annee": int(annee_active),
                            "compte": str(compte),
                            "budget": float(budget),
                        },
                        on_conflict="annee,compte",
                    ).execute()

                    st.success("Budget enregistré.")
                    st.rerun()

    # ======================================================
    # ✏️ MODIFIER
    # ======================================================
    with tab_modifier:
        df_mod = df[df["annee"] == annee_active]

        if df_mod.empty:
            st.info("Aucun budget à modifier pour cette année.")
        else:
            selection = st.selectbox(
                "Sélectionner un compte",
                df_mod["compte"].tolist(),
            )

            ligne = df_mod[df_mod["compte"] == selection].iloc[0]

            with st.form("modifier_budget"):
                nouveau_budget = st.number_input(
                    "Nouveau budget (€)",
                    value=float(ligne["budget"]),
                    min_value=0.0,
                    step=10.0,
                )

                submitted = st.form_submit_button("💾 Mettre à jour")

                if submitted:
                    supabase.table("budgets").update(
                        {"budget": float(nouveau_budget)}
                    ).eq("id", ligne["id"]).execute()

                    st.success("Budget modifié.")
                    st.rerun()

    # ======================================================
    # 🗑 SUPPRIMER
    # ======================================================
    with tab_supprimer:
        df_del = df[df["annee"] == annee_active]

        if df_del.empty:
            st.info("Aucun budget à supprimer pour cette année.")
        else:
            selection = st.selectbox(
                "Compte à supprimer",
                df_del["compte"].tolist(),
            )

            ligne = df_del[df_del["compte"] == selection].iloc[0]

            st.warning(
                f"Suppression définitive du budget **{selection} – {annee_active}**"
            )

            if st.button("🗑 Confirmer la suppression"):
                supabase.table("budgets").delete().eq("id", ligne["id"]).execute()
                st.success("Budget supprimé.")
                st.rerun()
