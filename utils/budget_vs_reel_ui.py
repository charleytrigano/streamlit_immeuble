import streamlit as st
import pandas as pd


def euro(x):
    if x is None:
        return "—"
    return f"{x:,.2f} €".replace(",", " ").replace(".", ",")


def pct(x):
    if x is None:
        return "—"
    return f"{x:.1f} %".replace(".", ",")


def budget_vs_reel_ui(supabase, annee):
    st.header("📊 Budget vs Réel")

    # =========================
    # CHARGEMENT DES DONNÉES
    # =========================
    dep = pd.DataFrame(
        supabase.table("depenses")
        .select("annee, compte, montant_ttc")
        .eq("annee", annee)
        .execute()
        .data
    )

    bud = pd.DataFrame(
        supabase.table("budgets")
        .select("annee, groupe_compte, libelle_groupe, budget")
        .eq("annee", annee)
        .execute()
        .data
    )

    plan = pd.DataFrame(
        supabase.table("plan_comptable")
        .select("compte_8, libelle, groupe_compte, libelle_groupe")
        .execute()
        .data
    )

    if dep.empty and bud.empty:
        st.info("Aucune donnée pour cette année.")
        return

    # =========================
    # RÉEL → GROUPE DE COMPTE
    # =========================
    dep = dep.merge(
        plan,
        left_on="compte",
        right_on="compte_8",
        how="left"
    )

    reel_grp = (
        dep.groupby(
            ["groupe_compte", "libelle_groupe"],
            dropna=False,
            as_index=False
        )
        .agg(reel=("montant_ttc", "sum"))
    )

    # =========================
    # BUDGET → GROUPE
    # =========================
    bud_grp = (
        bud.groupby(
            ["groupe_compte", "libelle_groupe"],
            dropna=False,
            as_index=False
        )
        .agg(budget=("budget", "sum"))
    )

    # =========================
    # MERGE FINAL
    # =========================
    final = pd.merge(
        bud_grp,
        reel_grp,
        on=["groupe_compte", "libelle_groupe"],
        how="outer"
    ).fillna(0)

    final["ecart"] = final["reel"] - final["budget"]
    final["ecart_pct"] = final.apply(
        lambda r: None if r["budget"] == 0 else (r["ecart"] / r["budget"] * 100),
        axis=1
    )

    final = final.sort_values("groupe_compte")

    # =========================
    # KPIs
    # =========================
    c1, c2, c3, c4 = st.columns(4)

    total_budget = final["budget"].sum()
    total_reel = final["reel"].sum()
    total_ecart = total_reel - total_budget
    total_pct = None if total_budget == 0 else total_ecart / total_budget * 100

    c1.metric("Budget total", euro(total_budget))
    c2.metric("Dépenses réelles", euro(total_reel))
    c3.metric("Écart", euro(total_ecart))
    c4.metric("Écart %", pct(total_pct))

    # =========================
    # TABLEAU 1 — BUDGET vs RÉEL
    # =========================
    st.subheader("📘 Budget vs Réel par groupe")

    df_aff = final.copy()
    df_aff["Budget"] = df_aff["budget"].apply(euro)
    df_aff["Réel"] = df_aff["reel"].apply(euro)
    df_aff["Écart €"] = df_aff["ecart"].apply(euro)
    df_aff["Écart %"] = df_aff["ecart_pct"].apply(pct)

    st.dataframe(
        df_aff[[
            "groupe_compte",
            "libelle_groupe",
            "Budget",
            "Réel",
            "Écart €",
            "Écart %"
        ]],
        use_container_width=True
    )

    # =========================
    # TABLEAU 2 — DÉTAIL DU RÉEL
    # =========================
    st.subheader("🔎 Détail du réel (audit)")

    detail = (
        dep.groupby(
            ["groupe_compte", "compte", "libelle"],
            as_index=False
        )
        .agg(reel=("montant_ttc", "sum"))
        .sort_values(["groupe_compte", "reel"], ascending=[True, False])
    )

    detail["Réel"] = detail["reel"].apply(euro)

    st.dataframe(
        detail[[
            "groupe_compte",
            "compte",
            "libelle",
            "Réel"
        ]],
        use_container_width=True
    )