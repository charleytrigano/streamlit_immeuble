import streamlit as st
import pandas as pd


def budget_vs_reel_ui(supabase, annee: int):
    st.header(f"📊 Budget vs Réel – {annee}")

    # =====================================================
    # 1️⃣ CHARGEMENT BUDGETS
    # =====================================================
    try:
        r_budget = (
            supabase
            .table("budgets")
            .select(
                "annee, groupe_compte, groupe_charges, budget, libelle_groupe"
            )
            .eq("annee", annee)
            .execute()
        )
    except Exception as e:
        st.error("❌ Erreur chargement budgets")
        st.exception(e)
        return

    if not r_budget.data:
        st.warning("Aucun budget pour cette année")
        return

    df_budget = pd.DataFrame(r_budget.data)

    # 👉 budget UNIQUE par groupe_compte
    df_budget_grp = (
        df_budget
        .groupby(["groupe_compte", "groupe_charges", "libelle_groupe"], as_index=False)
        .agg({"budget": "sum"})
    )

    # =====================================================
    # 2️⃣ CHARGEMENT DÉPENSES RÉELLES
    # =====================================================
    try:
        r_dep = (
            supabase
            .table("v_depenses_enrichies")
            .select(
                "annee, groupe_compte, groupe_charges, montant_ttc"
            )
            .eq("annee", annee)
            .execute()
        )
    except Exception as e:
        st.error("❌ Erreur chargement dépenses")
        st.exception(e)
        return

    if not r_dep.data:
        st.warning("Aucune dépense pour cette année")
        return

    df_dep = pd.DataFrame(r_dep.data)

    df_dep_grp = (
        df_dep
        .groupby(["groupe_compte", "groupe_charges"], as_index=False)
        .agg(reel=("montant_ttc", "sum"))
    )

    # =====================================================
    # 3️⃣ MERGE BUDGET / RÉEL
    # =====================================================
    df = df_budget_grp.merge(
        df_dep_grp,
        on=["groupe_compte", "groupe_charges"],
        how="left"
    )

    df["reel"] = df["reel"].fillna(0.0)
    df["ecart"] = df["budget"] - df["reel"]

    # =====================================================
    # 4️⃣ FILTRE GROUPE DE CHARGES (SANS DUPLICATION)
    # =====================================================
    groupes = ["Tous"] + sorted(
        df["groupe_charges"].dropna().unique().tolist()
    )

    groupe_sel = st.selectbox(
        "Groupe de charges",
        groupes,
        key="bvr_groupe_charges"
    )

    if groupe_sel != "Tous":
        df = df[df["groupe_charges"] == groupe_sel]

    # =====================================================
    # 5️⃣ TABLEAU
    # =====================================================
    st.dataframe(
        df[[
            "groupe_charges",
            "groupe_compte",
            "libelle_groupe",
            "budget",
            "reel",
            "ecart"
        ]].sort_values(["groupe_charges", "groupe_compte"]),
        use_container_width=True
    )

    # =====================================================
    # 6️⃣ KPI — CALCUL CORRECT (SANS DOUBLE COMPTAGE)
    # =====================================================
    # ⚠️ Budget = somme UNIQUE AVANT jointure
    budget_total = df_budget_grp["budget"].sum()

    # Réel = somme après filtres
    reel_total = df["reel"].sum()

    ecart_total = budget_total - reel_total

    st.divider()

    c1, c2, c3 = st.columns(3)
    c1.metric("💰 Budget", f"{budget_total:,.2f} €")
    c2.metric("📄 Réel", f"{reel_total:,.2f} €")
    c3.metric("📊 Écart", f"{ecart_total:,.2f} €")