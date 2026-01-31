import streamlit as st
import pandas as pd


def budget_vs_reel_ui(supabase, annee):
    st.title(f"📊 Budget vs Réel – {annee}")

    # ===============================
    # CHARGEMENT DES BUDGETS
    # ===============================
    try:
        r_budget = (
            supabase
            .table("budgets")
            .select("annee, groupe_compte, libelle_groupe, budget")
            .eq("annee", annee)
            .execute()
        )
    except Exception as e:
        st.error("❌ Erreur lecture table budgets")
        st.exception(e)
        return

    if not r_budget.data:
        st.warning("Aucun budget trouvé pour cette année")
        return

    df_budget = pd.DataFrame(r_budget.data)
    df_budget["budget"] = pd.to_numeric(df_budget["budget"], errors="coerce").fillna(0)

    # ===============================
    # CHARGEMENT DES DÉPENSES RÉELLES
    # ===============================
    try:
        r_dep = (
            supabase
            .table("v_depenses_enrichies")
            .select("annee, groupe_compte, groupe_charges, montant_ttc")
            .eq("annee", annee)
            .execute()
        )
    except Exception as e:
        st.error("❌ Erreur lecture des dépenses")
        st.exception(e)
        return

    if not r_dep.data:
        st.warning("Aucune dépense trouvée pour cette année")
        return

    df_dep = pd.DataFrame(r_dep.data)
    df_dep["montant_ttc"] = pd.to_numeric(df_dep["montant_ttc"], errors="coerce").fillna(0)

    # ===============================
    # AGRÉGATION
    # ===============================
    df_budget_grp = (
        df_budget
        .groupby(["groupe_compte", "libelle_groupe"], as_index=False)
        .agg(budget=("budget", "sum"))
    )

    df_dep_grp = (
        df_dep
        .groupby(["groupe_charges", "groupe_compte"], as_index=False)
        .agg(reel=("montant_ttc", "sum"))
    )

    # ===============================
    # MERGE BUDGET / RÉEL
    # ===============================
    df = pd.merge(
        df_dep_grp,
        df_budget_grp,
        on="groupe_compte",
        how="left"
    )

    df["budget"] = df["budget"].fillna(0)
    df["ecart"] = df["budget"] - df["reel"]

    # ===============================
    # FILTRE GROUPE DE CHARGES
    # ===============================
    groupes = ["Tous"] + sorted(df["groupe_charges"].dropna().unique().tolist())

    groupe_sel = st.selectbox(
        "Groupe de charges",
        groupes,
        key="bvr_filtre_groupe_charges"
    )

    if groupe_sel != "Tous":
        df = df[df["groupe_charges"] == groupe_sel]

    # ===============================
    # AFFICHAGE TABLEAU
    # ===============================
    st.dataframe(
        df[
            [
                "groupe_charges",
                "groupe_compte",
                "libelle_groupe",
                "budget",
                "reel",
                "ecart"
            ]
        ],
        use_container_width=True,
        hide_index=True
    )

    # ===============================
    # KPI
    # ===============================
    col1, col2, col3 = st.columns(3)
    col1.metric("💰 Budget", f"{df['budget'].sum():,.2f} €")
    col2.metric("📄 Réel", f"{df['reel'].sum():,.2f} €")
    col3.metric("📊 Écart", f"{df['ecart'].sum():,.2f} €")