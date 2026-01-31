import streamlit as st
import pandas as pd

def euro(x):
    return f"{x:,.2f} €".replace(",", " ").replace(".", ",")

def budget_vs_reel_ui(supabase, annee):
    st.subheader(f"📊 Budget vs Réel – {annee}")

    # ======================================================
    # CHARGEMENT DES DONNÉES
    # ======================================================
    bud_resp = (
        supabase
        .table("budget")
        .select("annee, groupe_compte, budget")
        .eq("annee", annee)
        .execute()
    )

    dep_resp = (
        supabase
        .table("v_depenses_enrichies")
        .select("annee, groupe_compte, groupe_charges, montant_ttc")
        .eq("annee", annee)
        .execute()
    )

    if not bud_resp.data or not dep_resp.data:
        st.warning("Aucune donnée budget ou dépenses pour cette année.")
        return

    df_bud = pd.DataFrame(bud_resp.data)
    df_dep = pd.DataFrame(dep_resp.data)

    # ======================================================
    # FILTRE GROUPE DE CHARGES
    # ======================================================
    groupes = ["Tous"] + sorted(
        df_dep["groupe_charges"].dropna().unique().tolist()
    )

    groupe_sel = st.selectbox(
        "Groupe de charges",
        groupes,
        key="filtre_budget_vs_reel_groupe_charges"
    )

    if groupe_sel != "Tous":
        df_dep = df_dep[df_dep["groupe_charges"] == groupe_sel]

    # ======================================================
    # AGRÉGATIONS
    # ======================================================
    dep_group = (
        df_dep
        .groupby(["groupe_charges", "groupe_compte"], as_index=False)
        .agg(reel=("montant_ttc", "sum"))
    )

    bud_group = (
        df_bud
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
    df["ecart_pct"] = df.apply(
        lambda r: (r["ecart"] / r["budget"] * 100) if r["budget"] != 0 else 0,
        axis=1
    )

    # ======================================================
    # KPI
    # ======================================================
    total_budget = df["budget"].sum()
    total_reel = df["reel"].sum()
    total_ecart = total_budget - total_reel

    c1, c2, c3 = st.columns(3)
    c1.metric("Budget total", euro(total_budget))
    c2.metric("Réel", euro(total_reel))
    c3.metric("Écart", euro(total_ecart))

    # ======================================================
    # TABLEAU FINAL
    # ======================================================
    st.markdown("### 📋 Détail Budget vs Réel")

    st.dataframe(
        df.rename(columns={
            "groupe_charges": "Groupe de charges",
            "groupe_compte": "Groupe de compte",
            "budget": "Budget",
            "reel": "Réel",
            "ecart": "Écart",
            "ecart_pct": "Écart (%)"
        }),
        use_container_width=True
    )