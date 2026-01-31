import streamlit as st
import pandas as pd


def budget_vs_reel_ui(supabase, annee):
    st.header(f"📊 Budget vs Réel – {annee}")

    # =========================
    # CHARGEMENT BUDGETS
    # =========================
    r_budget = (
        supabase
        .table("budgets")
        .select("annee, groupe_compte, budget")
        .eq("annee", annee)
        .execute()
    )

    if not r_budget.data:
        st.warning("Aucun budget trouvé pour cette année.")
        return

    df_budget = pd.DataFrame(r_budget.data)

    # =========================
    # CHARGEMENT DÉPENSES (VUE ENRICHIE)
    # =========================
    r_dep = (
        supabase
        .table("v_depenses_enrichies")
        .select("""
            annee,
            groupe_compte,
            groupe_charges,
            montant_ttc
        """)
        .eq("annee", annee)
        .execute()
    )

    if not r_dep.data:
        st.warning("Aucune dépense trouvée pour cette année.")
        return

    df_dep = pd.DataFrame(r_dep.data)

    # =========================
    # FILTRE GROUPE DE CHARGES
    # =========================
    groupes_charges = ["Tous"] + sorted(
        df_dep["groupe_charges"].dropna().unique().tolist()
    )

    groupe_sel = st.selectbox(
        "Groupe de charges",
        groupes_charges,
        key="bvr_groupe_charges"
    )

    if groupe_sel != "Tous":
        df_dep = df_dep[df_dep["groupe_charges"] == groupe_sel]

    # =========================
    # AGRÉGATION
    # =========================
    dep_group = (
        df_dep
        .groupby(["groupe_charges", "groupe_compte"], as_index=False)
        .agg(reel=("montant_ttc", "sum"))
    )

    bud_group = (
        df_budget
        .groupby("groupe_compte", as_index=False)
        .agg(budget=("budget", "sum"))
    )

    df = dep_group.merge(
        bud_group,
        on="groupe_compte",
        how="left"
    )

    df["budget"] = df["budget"].fillna(0)
    df["ecart"] = df["budget"] - df["reel"]

    # =========================
    # SOUS-TOTAUX PAR GROUPE DE CHARGES
    # =========================
    total_groupes = (
        df
        .groupby("groupe_charges", as_index=False)
        .agg(
            budget=("budget", "sum"),
            reel=("reel", "sum"),
            ecart=("ecart", "sum")
        )
    )

    total_groupes["groupe_compte"] = "TOTAL"

    df_final = pd.concat(
        [df, total_groupes],
        ignore_index=True
    )

    # =========================
    # AFFICHAGE
    # =========================
    st.subheader("📋 Comparaison Budget / Réel")

    st.dataframe(
        df_final.sort_values(["groupe_charges", "groupe_compte"]),
        use_container_width=True
    )

    # =========================
    # KPI GLOBAUX
    # =========================
    total_budget = df["budget"].sum()
    total_reel = df["reel"].sum()
    total_ecart = total_budget - total_reel

    c1, c2, c3 = st.columns(3)
    c1.metric("Budget total (€)", f"{total_budget:,.2f}")
    c2.metric("Réel total (€)", f"{total_reel:,.2f}")
    c3.metric("Écart (€)", f"{total_ecart:,.2f}")