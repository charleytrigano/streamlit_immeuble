import streamlit as st
import pandas as pd
import plotly.express as px


def statistiques_ui(supabase):
    st.title("📊 Statistiques")

    # -----------------------------
    # Filtres globaux
    # -----------------------------
    annee = st.selectbox("Année", [2023, 2024, 2025, 2026])

    tab1, tab2 = st.tabs(["📈 Vue globale", "📊 Budget vs Réel"])

    # =========================================================
    # 📈 VUE GLOBALE
    # =========================================================
    with tab1:
        dep_resp = (
            supabase
            .table("depenses")
            .select("annee, compte, fournisseur, type, montant_ttc, date")
            .eq("annee", annee)
            .execute()
        )

        if not dep_resp.data:
            st.warning("Aucune dépense pour cette année.")
            return

        df = pd.DataFrame(dep_resp.data)
        df["montant_ttc"] = df["montant_ttc"].astype(float)
        df["date"] = pd.to_datetime(df["date"], errors="coerce")

        # ---------- Groupe de compte
        def groupe(compte):
            if compte in {"6211", "6213", "6222", "6223"}:
                return compte[:4]
            return compte[:3]

        df["groupe_compte"] = df["compte"].astype(str).apply(groupe)

        # ---------- Filtres
        fournisseurs = st.multiselect(
            "Fournisseur",
            sorted(df["fournisseur"].dropna().unique())
        )

        types = st.multiselect(
            "Type",
            ["Charge", "Remboursement", "Avoir"]
        )

        if fournisseurs:
            df = df[df["fournisseur"].isin(fournisseurs)]
        if types:
            df = df[df["type"].isin(types)]

        # ---------- KPI
        total = df["montant_ttc"].sum()
        nb = len(df)
        moy = total / nb if nb else 0

        c1, c2, c3 = st.columns(3)
        c1.metric("Total dépenses (€)", f"{total:,.2f}")
        c2.metric("Nombre de lignes", nb)
        c3.metric("Dépense moyenne (€)", f"{moy:,.2f}")

        # ---------- GRAPHIQUE 1 : Répartition par groupe
        grp = (
            df.groupby("groupe_compte", as_index=False)
            .agg(total=("montant_ttc", "sum"))
        )

        fig_pie = px.pie(
            grp,
            names="groupe_compte",
            values="total",
            title="Répartition des dépenses par groupe de compte"
        )
        st.plotly_chart(fig_pie, use_container_width=True)

        # ---------- GRAPHIQUE 2 : Top fournisseurs
        top_f = (
            df.groupby("fournisseur", as_index=False)
            .agg(total=("montant_ttc", "sum"))
            .sort_values("total", ascending=False)
            .head(10)
        )

        fig_bar = px.bar(
            top_f,
            x="fournisseur",
            y="total",
            title="Top 10 fournisseurs",
            labels={"total": "Montant (€)"}
        )
        st.plotly_chart(fig_bar, use_container_width=True)

        # ---------- GRAPHIQUE 3 : Évolution mensuelle
        if df["date"].notna().any():
            df["mois"] = df["date"].dt.to_period("M").astype(str)

            mensuel = (
                df.groupby("mois", as_index=False)
                .agg(total=("montant_ttc", "sum"))
            )

            fig_line = px.line(
                mensuel,
                x="mois",
                y="total",
                title="Évolution mensuelle des dépenses",
                markers=True
            )
            st.plotly_chart(fig_line, use_container_width=True)

        st.dataframe(df, use_container_width=True)

    # =========================================================
    # 📊 BUDGET VS RÉEL
    # =========================================================
    with tab2:
        budget_resp = (
            supabase
            .table("budgets")
            .select("annee, groupe_compte, budget")
            .eq("annee", annee)
            .execute()
        )

        if not budget_resp.data:
            st.warning("Aucun budget pour cette année.")
            return

        df_budget = pd.DataFrame(budget_resp.data)
        df_budget["budget"] = df_budget["budget"].astype(float)

        df_budget = (
            df_budget
            .groupby("groupe_compte", as_index=False)
            .agg(budget=("budget", "sum"))
        )

        dep_resp = (
            supabase
            .table("depenses")
            .select("annee, compte, montant_ttc")
            .eq("annee", annee)
            .execute()
        )

        if not dep_resp.data:
            st.warning("Aucune dépense pour cette année.")
            return

        df_dep = pd.DataFrame(dep_resp.data)
        df_dep["montant_ttc"] = df_dep["montant_ttc"].astype(float)

        df_dep["groupe_compte"] = df_dep["compte"].astype(str).apply(
            lambda c: c[:4] if c in {"6211", "6213", "6222", "6223"} else c[:3]
        )

        df_dep = (
            df_dep
            .groupby("groupe_compte", as_index=False)
            .agg(reel=("montant_ttc", "sum"))
        )

        df = pd.merge(df_budget, df_dep, on="groupe_compte", how="outer").fillna(0)

        df["ecart"] = df["budget"] - df["reel"]
        df["ecart_pct"] = df.apply(
            lambda r: (r["ecart"] / r["budget"] * 100) if r["budget"] else 0,
            axis=1
        )

        # KPI
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Budget (€)", f"{df['budget'].sum():,.2f}")
        c2.metric("Réel (€)", f"{df['reel'].sum():,.2f}")
        c3.metric("Écart (€)", f"{df['ecart'].sum():,.2f}")
        c4.metric(
            "Écart (%)",
            f"{(df['ecart'].sum() / df['budget'].sum() * 100) if df['budget'].sum() else 0:.2f}%"
        )

        # Graphique Budget vs Réel
        fig_bvr = px.bar(
            df,
            x="groupe_compte",
            y=["budget", "reel"],
            barmode="group",
            title="Budget vs Réel par groupe de compte"
        )
        st.plotly_chart(fig_bvr, use_container_width=True)

        st.dataframe(df.sort_values("groupe_compte"), use_container_width=True)
