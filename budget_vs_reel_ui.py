import streamlit as st
import pandas as pd

def euro(x):
    if pd.isna(x):
        return "0,00 €"
    return f"{x:,.2f} €".replace(",", " ").replace(".", ",")


def budget_vs_reel_ui(supabase, annee):
    st.subheader(f"📊 Budget vs Réel – {annee}")

    # =====================================================
    # CHARGEMENT DU RÉEL (vue enrichie)
    # =====================================================
    rep_reel = (
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

    if not rep_reel.data:
        st.warning("Aucune dépense pour cette année.")
        return

    df_reel = pd.DataFrame(rep_reel.data)

    # =====================================================
    # CHARGEMENT DU BUDGET
    # =====================================================
    rep_bud = (
        supabase
        .table("budgets")
        .select("""
            annee,
            groupe_compte,
            groupe_charges,
            budget
        """)
        .eq("annee", annee)
        .execute()
    )

    if not rep_bud.data:
        st.warning("Aucun budget pour cette année.")
        return

    df_bud = pd.DataFrame(rep_bud.data)

    # =====================================================
    # FILTRE GROUPE DE CHARGES
    # =====================================================
    groupes_charges = (
        ["Tous"]
        + sorted(
            set(df_reel["groupe_charges"].dropna().unique())
            | set(df_bud["groupe_charges"].dropna().unique())
        )
    )

    groupe_sel = st.selectbox(
        "Groupe de charges",
        groupes_charges,
        key="filtre_groupe_charges_bvr"
    )

    if groupe_sel != "Tous":
        df_reel = df_reel[df_reel["groupe_charges"] == groupe_sel]
        df_bud = df_bud[df_bud["groupe_charges"] == groupe_sel]

    # =====================================================
    # AGRÉGATIONS
    # =====================================================
    reel_grp = (
        df_reel
        .groupby(["groupe_charges", "groupe_compte"], as_index=False)
        .agg(reel=("montant_ttc", "sum"))
    )

    bud_grp = (
        df_bud
        .groupby(["groupe_charges", "groupe_compte"], as_index=False)
        .agg(budget=("budget", "sum"))
    )

    # =====================================================
    # MERGE BUDGET / RÉEL
    # =====================================================
    df = pd.merge(
        bud_grp,
        reel_grp,
        on=["groupe_charges", "groupe_compte"],
        how="outer"
    ).fillna(0)

    df["écart"] = df["budget"] - df["reel"]
    df["% écart"] = df.apply(
        lambda r: (r["écart"] / r["budget"] * 100) if r["budget"] != 0 else 0,
        axis=1
    )

    # =====================================================
    # KPI GLOBAUX
    # =====================================================
    col1, col2, col3, col4 = st.columns(4)

    col1.metric("Budget", euro(df["budget"].sum()))
    col2.metric("Réel", euro(df["reel"].sum()))
    col3.metric("Écart", euro(df["écart"].sum()))

    pct = (
        df["écart"].sum() / df["budget"].sum() * 100
        if df["budget"].sum() != 0 else 0
    )
    col4.metric("% écart", f"{pct:.2f} %")

    # =====================================================
    # TABLEAU DÉTAILLÉ
    # =====================================================
    st.markdown("### 📋 Détail par groupe de comptes")

    df_aff = df.copy()
    df_aff["budget"] = df_aff["budget"].apply(euro)
    df_aff["reel"] = df_aff["reel"].apply(euro)
    df_aff["écart"] = df_aff["écart"].apply(euro)
    df_aff["% écart"] = df_aff["% écart"].map(lambda x: f"{x:.2f} %")

    df_aff = df_aff.sort_values(["groupe_charges", "groupe_compte"])

    st.dataframe(df_aff, use_container_width=True)