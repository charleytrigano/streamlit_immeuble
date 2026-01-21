import streamlit as st
import pandas as pd


def budget_ui(supabase):
    st.header("💰 Budget")

    tabs = st.tabs(["📊 Consulter", "➕ Ajouter", "✏️ Modifier", "🗑 Supprimer"])

    # ======================================================
    # 📊 CONSULTER
    # ======================================================
    with tabs[0]:
        df = pd.DataFrame(
            supabase.table("budgets").select("*").execute().data
        )

        if df.empty:
            st.info("Aucun budget enregistré.")
            return

        # ---------- FILTRES ----------
        f1, f2 = st.columns(2)

        with f1:
            annee = st.selectbox(
                "Année",
                sorted(df["annee"].unique())
            )

        with f2:
            compte = st.selectbox(
                "Compte",
                ["Tous"] + sorted(df["compte"].unique())
            )

        df = df[df["annee"] == annee]
        if compte != "Tous":
            df = df[df["compte"] == compte]

        # ---------- KPI ----------
        k1, k2 = st.columns(2)
        k1.metric("Budget total (€)", f"{df['budget'].sum():,.0f}")
        k2.metric("Nombre de comptes", len(df))

        st.dataframe(df, use_container_width=True)

    # ======================================================
    # ➕ AJOUTER
    # ======================================================
    with tabs[1]:
        with st.form("add_budget"):
            annee = st.number_input("Année", value=2025)
            compte = st.text_input("Compte")
            budget = st.number_input("Budget (€)", step=100.0)

            if st.form_submit_button("Enregistrer"):
                supabase.table("budgets").upsert({
                    "annee": annee,
                    "compte": compte,
                    "budget": budget
                }).execute()

                st.success("Budget enregistré")

    # ======================================================
    # ✏️ MODIFIER
    # ======================================================
    with tabs[2]:
        bud_id = st.selectbox("Budget", df["id"])

        val = df[df["id"] == bud_id].iloc[0]["budget"]

        new_val = st.number_input("Nouveau budget", value=float(val))

        if st.button("Mettre à jour"):
            supabase.table("budgets") \
                .update({"budget": new_val}) \
                .eq("id", bud_id) \
                .execute()

            st.success("Budget mis à jour")

    # ======================================================
    # 🗑 SUPPRIMER
    # ======================================================
    with tabs[3]:
        bud_id = st.selectbox("Budget à supprimer", df["id"])

        if st.button("Supprimer"):
            supabase.table("budgets").delete().eq("id", bud_id).execute()
            st.success("Budget supprimé")