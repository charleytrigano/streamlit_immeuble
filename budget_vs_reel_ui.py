import streamlit as st
import pandas as pd


def euro(x):
    if x is None:
        return "0,00 €"
    return f"{x:,.2f} €".replace(",", " ").replace(".", ",")


def budget_vs_reel_ui(supabase, annee):
    st.subheader(f"📊 Budget vs Réel – {annee}")

    # =====================================================
    # CHARGEMENT DU BUDGET (par groupe_compte / groupe_charges)
    # =====================================================
    bud_resp = (
        supabase
        .table("budgets")
        .select("groupe_compte, groupe_charges, budget")
        .eq("annee", annee)
        .execute()
    )

    if not bud_resp.data:
        st.warning("Aucun budget pour cette année.")
        return

    df_budget = pd.DataFrame(bud_resp.data)

    # =====================================================
    # CHARGEMENT DU RÉEL (vue enrichie)
    # =====================================================
    dep_resp = (
        supabase
        .table("v_depenses_enrichies")
        .select("groupe_compte, groupe_charges, montant_ttc")
        .eq("annee", annee)
        .execute()
    )

    if not dep_resp.data:
        st.warning("Aucune dépense pour cette année.")
        return

    df_dep = pd.DataFrame(dep_resp.data)

    # =====================================================
    # AGRÉGATIONS
    # =====================================================
    bud_grp = (
        df_budget
        .groupby(["groupe_charges", "groupe_compte"], as_index=False)
        .agg(budget=("budget", "sum"))
    )

    dep_grp = (
        df_dep
        .groupby(["groupe_charges", "groupe_compte"], as_index=False)
        .agg(reel=("montant_ttc", "sum"))
    )

    df = bud_grp.merge(
        dep_grp,
        on=["groupe_charges", "groupe_compte"],
        how="left"
    )

    df["reel"] = df["reel"].fillna(0)
    df["ecart"] = df["budget"] - df["reel"]
    df["ecart_pct"] = df.apply(
        lambda r: (r["ecart"] / r["budget"] * 100) if r["budget"] != 0 else 0,
        axis=1
    )

    # =====================================================
    # KPI GLOBAUX
    # =====================================================
    budget_total = df["budget"].sum()
    reel_total = df["reel"].sum()
    ecart_total = budget_total - reel_total
    ecart_pct_total = (ecart_total / budget_total * 100) if budget_total else 0

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Budget total", euro(budget_total))
    c2.metric("Réel total", euro(reel_total))
    c3.metric("Écart", euro(ecart_total))
    c4.metric("Écart %", f"{ecart_pct_total:.2f} %")

    # =====================================================
    # LOI ALUR – 5 %
    # =====================================================
    loi_alur = budget_total * 0.05
    st.markdown("### ⚖️ Loi ALUR")
    st.metric("Provision Loi ALUR (5 %)", euro(loi_alur))

    # =====================================================
    # SYNTHÈSE PAR GROUPE DE CHARGES
    # =====================================================
    st.markdown("### 🧾 Synthèse par groupe de charges")

    synthese = (
        df
        .groupby("groupe_charges", as_index=False)
        .agg(
            Budget=("budget", "sum"),
            Réel=("reel", "sum")
        )
    )

    synthese["Écart"] = synthese["Budget"] - synthese["Réel"]
    synthese["Écart %"] = synthese.apply(
        lambda r: (r["Écart"] / r["Budget"] * 100) if r["Budget"] != 0 else 0,
        axis=1
    )

    st.dataframe(
        synthese.style.format({
            "Budget": euro,
            "Réel": euro,
            "Écart": euro,
            "Écart %": "{:.2f} %"
        }),
        use_container_width=True
    )

    # =====================================================
    # DÉTAIL PAR GROUPE DE COMPTES
    # =====================================================
    st.markdown("### 🔍 Détail par groupe de comptes")

    detail = df.sort_values(["groupe_charges", "groupe_compte"])

    st.dataframe(
        detail.rename(columns={
            "groupe_charges": "Groupe de charges",
            "groupe_compte": "Groupe de compte",
            "budget": "Budget",
            "reel": "Réel",
            "ecart": "Écart",
            "ecart_pct": "Écart %"
        }).style.format({
            "Budget": euro,
            "Réel": euro,
            "Écart": euro,
            "Écart %": "{:.2f} %"
        }),
        use_container_width=True
    )