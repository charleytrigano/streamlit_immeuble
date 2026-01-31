import streamlit as st
import pandas as pd

# =========================================================
# BUDGET VS RÉEL
# =========================================================
def budget_vs_reel_ui(supabase, annee):

    st.header(f"📊 Budget vs Réel – {annee}")

    try:
        # =========================
        # BUDGET (TABLE budgets)
        # =========================
        r_budget = (
            supabase
            .table("budgets")
            .select(
                "annee, groupe_charges, groupe_compte, montant"
            )
            .eq("annee", annee)
            .execute()
        )

        if not r_budget.data:
            st.warning("Aucune donnée budget")
            return

        df_budget = pd.DataFrame(r_budget.data)
        df_budget.rename(columns={"montant": "budget"}, inplace=True)

        # =========================
        # RÉEL (VUE v_depenses_enrichies)
        # =========================
        r_dep = (
            supabase
            .table("v_depenses_enrichies")
            .select(
                "annee, groupe_charges, groupe_compte, montant_ttc"
            )
            .eq("annee", annee)
            .execute()
        )

        if not r_dep.data:
            st.warning("Aucune dépense réelle")
            return

        df_dep = pd.DataFrame(r_dep.data)
        df_dep.rename(columns={"montant_ttc": "reel"}, inplace=True)

        # =========================
        # FILTRE GROUPE DE CHARGES
        # =========================
        groupes = ["Tous"] + sorted(df_budget["groupe_charges"].dropna().unique())

        groupe_sel = st.selectbox(
            "Groupe de charges",
            groupes,
            key="budget_vs_reel_groupe_charges"
        )

        if groupe_sel != "Tous":
            df_budget = df_budget[df_budget["groupe_charges"] == groupe_sel]
            df_dep = df_dep[df_dep["groupe_charges"] == groupe_sel]

        # =========================
        # AGRÉGATION
        # =========================
        budget_grp = (
            df_budget
            .groupby(["groupe_charges", "groupe_compte"], as_index=False)
            .agg({"budget": "sum"})
        )

        reel_grp = (
            df_dep
            .groupby(["groupe_charges", "groupe_compte"], as_index=False)
            .agg({"reel": "sum"})
        )

        df = pd.merge(
            budget_grp,
            reel_grp,
            on=["groupe_charges", "groupe_compte"],
            how="outer"
        ).fillna(0)

        df["écart"] = df["budget"] - df["reel"]

        # =========================
        # AFFICHAGE
        # =========================
        st.dataframe(
            df.sort_values(["groupe_charges", "groupe_compte"]),
            use_container_width=True
        )

        # =========================
        # KPI
        # =========================
        c1, c2, c3 = st.columns(3)

        c1.metric("Budget total", f"{df['budget'].sum():,.2f} €")
        c2.metric("Réel total", f"{df['reel'].sum():,.2f} €")
        c3.metric("Écart", f"{df['écart'].sum():,.2f} €")

    except Exception as e:
        st.error("❌ Erreur dans Budget vs Réel")
        st.exception(e)