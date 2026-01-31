import streamlit as st
import pandas as pd


def budget_vs_reel_ui(supabase, annee: int):
    st.title(f"📊 Budget vs Réel – {annee}")

    # =========================================================
    # CHARGEMENT BUDGET
    # Table : budgets
    # Colonnes attendues :
    # - annee
    # - groupe_compte
    # - groupe_charges
    # - montant
    # =========================================================
    try:
        r_budget = (
            supabase
            .table("budgets")
            .select("annee, groupe_compte, groupe_charges, montant")
            .eq("annee", annee)
            .execute()
        )
    except Exception as e:
        st.error("❌ Erreur chargement budget")
        st.exception(e)
        return

    if not r_budget.data:
        st.warning("⚠️ Aucun budget pour cette année")
        return

    df_budget = pd.DataFrame(r_budget.data)
    df_budget["montant"] = pd.to_numeric(df_budget["montant"], errors="coerce").fillna(0)

    # =========================================================
    # CHARGEMENT RÉEL
    # Vue : v_depenses_enrichies
    # Colonnes attendues :
    # - annee
    # - groupe_compte
    # - groupe_charges
    # - montant_ttc
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
    # MERGE BUDGET / RÉEL
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
    groupes_charges = ["Tous"] + sorted(df["groupe_charges"].dropna().unique().tolist())

    groupe_sel = st.selectbox(
        "Filtrer par groupe de charges",
        groupes_charges,
        key="filtre_budget_vs_reel_groupe_charges"
    )

    if groupe_sel != "Tous":
        df = df[df["groupe_charges"] == groupe_sel]

    # =========================================================
    # TRI & AFFICHAGE
    # =========================================================
    df = df.sort_values(["groupe_charges", "groupe_compte"])

    st.subheader("📋 Détail Budget vs Réel")
    st.dataframe(
        df,
        use_container_width=True,
        hide_index=True
    )

    # =========================================================
    # TOTAUX
    # =========================================================
    col1, col2, col3 = st.columns(3)

    col1.metric("💰 Budget total", f"{df['budget'].sum():,.2f} €")
    col2.metric("💸 Réel total", f"{df['reel'].sum():,.2f} €")
    col3.metric("📉 Écart global", f"{df['écart'].sum():,.2f} €")