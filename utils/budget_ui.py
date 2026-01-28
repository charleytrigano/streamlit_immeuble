import streamlit as st
import pandas as pd


def euro(x):
    if pd.isna(x):
        return "0,00 €"
    return f"{x:,.2f} €".replace(",", " ").replace(".", ",")


def budget_ui(supabase, annee):
    st.header("💰 Budget annuel")

    # ⚠️ cast année en STRING pour compatibilité Supabase
    annee_str = str(annee)

    # =========================
    # CHARGEMENT DONNÉES
    # =========================
    budgets = (
        supabase
        .table("budgets")
        .select("*")
        .eq("annee", annee_str)
        .execute()
    )

    depenses = (
        supabase
        .table("depenses")
        .select("*")
        .eq("annee", annee_str)
        .execute()
    )

    df_bud = pd.DataFrame(budgets.data or [])
    df_dep = pd.DataFrame(depenses.data or [])

    # DEBUG VISUEL (TEMPORAIRE)
    st.caption(f"📌 Budgets trouvés : {len(df_bud)} lignes")

    if df_bud.empty:
        st.warning("Aucun budget défini pour cette année.")
        return

    # =========================
    # DÉPENSES PAR GROUPE
    # =========================
    if not df_dep.empty:
        dep_group = (
            df_dep
            .groupby("groupe_compte", dropna=False)["montant_ttc"]
            .sum()
            .reset_index()
            .rename(columns={"montant_ttc": "realise"})
        )
    else:
        dep_group = pd.DataFrame(columns=["groupe_compte", "realise"])

    # =========================
    # MERGE
    # =========================
    df = df_bud.merge(dep_group, on="groupe_compte", how="left")
    df["realise"] = df["realise"].fillna(0)

    df["ecart"] = df["budget"] - df["realise"]
    df["ecart_pct"] = df.apply(
        lambda r: (r["ecart"] / r["budget"] * 100) if r["budget"] else 0,
        axis=1
    )

    # =========================
    # KPI
    # =========================
    total_budget = df["budget"].sum()
    total_realise = df["realise"].sum()
    total_ecart = total_budget - total_realise
    pct_ecart = (total_ecart / total_budget * 100) if total_budget else 0

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Budget total", euro(total_budget))
    c2.metric("Dépenses réalisées", euro(total_realise))
    c3.metric("Écart", euro(total_ecart))
    c4.metric("Écart %", f"{pct_ecart:.1f} %")

    # =========================
    # TABLEAU
    # =========================
    st.subheader("Détail par groupe de comptes")

    df_display = df[[
        "groupe_compte",
        "libelle_groupe",
        "budget",
        "realise",
        "ecart",
        "ecart_pct"
    ]].copy()

    df_display["budget"] = df_display["budget"].apply(euro)
    df_display["realise"] = df_display["realise"].apply(euro)
    df_display["ecart"] = df_display["ecart"].apply(euro)
    df_display["ecart_pct"] = df_display["ecart_pct"].map(lambda x: f"{x:.1f} %")

    st.dataframe(df_display, use_container_width=True)