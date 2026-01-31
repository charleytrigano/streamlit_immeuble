import streamlit as st
import pandas as pd


def budget_vs_reel_ui(supabase, annee):
    st.title(f"📊 Budget vs Réel – {annee}")

    # ======================================================
    # CHARGEMENT BUDGETS (TABLE budgets)
    # ======================================================
    try:
        r_budget = (
            supabase
            .table("budgets")
            .select("annee, budget, groupe_compte, libelle_groupe")
            .eq("annee", annee)
            .execute()
        )
    except Exception as e:
        st.error("❌ Erreur chargement budgets")
        st.exception(e)
        return

    if not r_budget.data:
        st.warning("Aucun budget trouvé")
        return

    df_budget = pd.DataFrame(r_budget.data)

    # ======================================================
    # CHARGEMENT RÉEL (VUE v_depenses_enrichies)
    # ======================================================
    try:
        r_dep = (
            supabase
            .table("v_depenses_enrichies")
            .select("annee, montant_ttc, groupe_charges, groupe_compte")
            .eq("annee", annee)
            .execute()
        )
    except Exception as e:
        st.error("❌ Erreur chargement dépenses")
        st.exception(e)
        return

    if not r_dep.data:
        st.warning("Aucune dépense trouvée")
        return

    df_dep = pd.DataFrame(r_dep.data)

    # ======================================================
    # AGRÉGATIONS
    # ======================================================
    df_budget_grp = (
        df_budget
        .groupby(["groupe_compte", "libelle_groupe"], as_index=False)
        .agg(budget=("budget", "sum"))
    )

    df_reel_grp = (
        df_dep
        .groupby("groupe_compte", as_index=False)
        .agg(reel=("montant_ttc", "sum"))
    )

    # ======================================================
    # MERGE
    # ======================================================
    df = df_budget_grp.merge(
        df_reel_grp,
        on="groupe_compte",
        how="left"
    )

    df["reel"] = df["reel"].fillna(0)
    df["ecart"] = df["budget"] - df["reel"]

    # ======================================================
    # FILTRE GROUPE DE CHARGES (LOGIQUE)
    # ======================================================
    groupes = ["Tous"] + sorted(df["libelle_groupe"].dropna().unique().tolist())

    groupe_sel = st.selectbox(
        "Groupe de charges",
        groupes,
        key="filtre_budget_vs_reel_groupe"
    )

    if groupe_sel != "Tous":
        df = df[df["libelle_groupe"] == groupe_sel]

    # ======================================================
    # KPI
    # ======================================================
    col1, col2, col3 = st.columns(3)

    col1.metric("💰 Budget", f"{df['budget'].sum():,.2f} €")
    col2.metric("📄 Réel", f"{df['reel'].sum():,.2f} €")
    col3.metric("📉 Écart", f"{df['ecart'].sum():,.2f} €")

    # ======================================================
    # TABLE
    # ======================================================
    st.dataframe(
        df.sort_values("groupe_compte"),
        use_container_width=True
    )