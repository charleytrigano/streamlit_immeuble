import streamlit as st
import pandas as pd


def budget_vs_reel_ui(supabase, annee: int):
    st.title(f"📊 Budget vs Réel – {annee}")

    # =========================================================
    # BUDGETS
    # ⚠️ COLONNE = exercice (PAS annee)
    # =========================================================
    try:
        r_budget = (
            supabase
            .table("budgets")
            .select("exercice, groupe_compte, groupe_charges, montant")
            .eq("exercice", annee)
            .execute()
        )
    except Exception as e:
        st.error("❌ Erreur chargement budgets")
        st.exception(e)
        return

    if not r_budget.data:
        st.warning("⚠️ Aucun budget pour cette année")
        return

    df_budget = pd.DataFrame(r_budget.data)
    df_budget["montant"] = pd.to_numeric(df_budget["montant"], errors="coerce").fillna(0)

    # =========================================================
    # DÉPENSES RÉELLES
    # =========================================================
    try:
        r_dep = (
            supabase
            .table("v_depenses_enrichies")
            .select("annee, groupe_compte, groupe_charges, montant_ttc")
            .eq("annee", annee)
            .execute()
        )
    except Exception as e:
        st.error("❌ Erreur chargement dépenses réelles")
        st.exception(e)
        return

    if not r_dep.data:
        st.warning("⚠️ Aucune dépense pour cette année")
        return

    df_reel = pd.DataFrame(r_dep.data)
    df_reel["montant_ttc"] = pd.to_numeric(df_reel["montant_ttc"], errors="coerce").fillna(0)

    # =========================================================
    # AGRÉGATION
    # =========================================================
    df_budget_grp = (
        df_budget
        .groupby(["groupe_charges", "groupe_compte"], as_index=False)
        .agg(budget=("montant", "sum"))
    )

    df_reel_grp = (
        df_reel
        .groupby(["groupe_charges", "groupe_compte"], as_index=False)
        .agg(reel=("montant_ttc", "sum"))
    )

    # =========================================================
    # MERGE
    # =========================================================
    df = pd.merge(
        df_budget_grp,
        df_reel_grp,
        on=["groupe_charges", "groupe_compte"],
        how="outer"
    ).fillna(0)

    df["écart"] = df["budget"] - df["reel"]

    # =========================================================
    # FILTRE GROUPE DE CHARGES
    # =========================================================
    groupes = ["Tous"] + sorted(df["groupe_charges"].dropna().unique().tolist())

    groupe_sel = st.selectbox(
        "Groupe de charges",
        groupes,
        key="budget_vs_reel_filtre_groupe_charges"
    )

    if groupe_sel != "Tous":
        df = df[df["groupe_charges"] == groupe_sel]

    # =========================================================
    # AFFICHAGE
    # =========================================================
    st.dataframe(df, use_container_width=True, hide_index=True)

    col1, col2, col3 = st.columns(3)
    col1.metric("💰 Budget", f"{df['budget'].sum():,.2f} €")
    col2.metric("💸 Réel", f"{df['reel'].sum():,.2f} €")
    col3.metric("📉 Écart", f"{df['écart'].sum():,.2f} €")