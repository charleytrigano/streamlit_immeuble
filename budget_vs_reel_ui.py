import streamlit as st
import pandas as pd


def budget_vs_reel_ui(supabase, annee):
    st.subheader(f"📊 Budget vs Réel – {annee}")

    # =========================
    # Chargement réel (vue enrichie)
    # =========================
    dep = (
        supabase
        .table("v_depenses_enrichies")
        .select("groupe_compte, groupe_charges, montant_ttc")
        .eq("annee", annee)
        .execute()
    )

    if not dep.data:
        st.warning("Aucune dépense")
        return

    df_dep = pd.DataFrame(dep.data)

    # =========================
    # Chargement budget
    # =========================
    bud = (
        supabase
        .table("budgets")
        .select("groupe_compte, libelle_groupe, budget")
        .eq("annee", annee)
        .execute()
    )

    df_bud = pd.DataFrame(bud.data) if bud.data else pd.DataFrame(
        columns=["groupe_compte", "libelle_groupe", "budget"]
    )

    # =========================
    # Filtre groupe de charges
    # =========================
    groupes = ["Tous"] + sorted(df_dep["groupe_charges"].dropna().unique().tolist())

    groupe_sel = st.selectbox(
        "Groupe de charges",
        groupes,
        key="bvr_groupe_charges"
    )

    if groupe_sel != "Tous":
        df_dep = df_dep[df_dep["groupe_charges"] == groupe_sel]

    # =========================
    # Agrégation
    # =========================
    reel = (
        df_dep
        .groupby(["groupe_charges", "groupe_compte"], as_index=False)
        .agg(reel=("montant_ttc", "sum"))
    )

    budg = (
        df_bud
        .groupby("groupe_compte", as_index=False)
        .agg(budget=("budget", "sum"))
    )

    df = reel.merge(budg, on="groupe_compte", how="left")
    df["budget"] = df["budget"].fillna(0)
    df["écart"] = df["reel"] - df["budget"]
    df["écart_%"] = df.apply(
        lambda r: (r["écart"] / r["budget"] * 100) if r["budget"] != 0 else 0,
        axis=1
    )

    # =========================
    # Tableau
    # =========================
    st.dataframe(
        df.sort_values(["groupe_charges", "groupe_compte"]),
        use_container_width=True
    )

    # =========================
    # Totaux
    # =========================
    st.markdown("### 📊 Totaux")

    col1, col2, col3 = st.columns(3)

    col1.metric("Total Budget", f"{df['budget'].sum():,.2f} €")
    col2.metric("Total Réel", f"{df['reel'].sum():,.2f} €")
    col3.metric("Écart global", f"{(df['reel'].sum() - df['budget'].sum()):,.2f} €")