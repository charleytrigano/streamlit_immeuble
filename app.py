import streamlit as st
import pandas as pd
from utils.supabase_client import get_supabase

# ======================================================
# CONFIG
# ======================================================
st.set_page_config(
    page_title="Pilotage des charges",
    layout="wide",
)

st.title("Pilotage des charges de l’immeuble")

supabase = get_supabase()

# ======================================================
# NAVIGATION
# ======================================================
page = st.sidebar.radio(
    "Navigation",
    [
        "💰 Budget",
        "📊 Budget vs Réel",
    ],
)

# ======================================================
# 💰 BUDGET — PRODUIT FINI
# ======================================================
if page == "💰 Budget":

    st.header("💰 Budget")

    # ---------- Chargement ----------
    bud_data = supabase.table("budgets").select("*").execute().data or []
    df_bud = pd.DataFrame(bud_data)

    if not df_bud.empty:
        df_bud["annee"] = df_bud["annee"].astype(int)
        df_bud["compte"] = df_bud["compte"].astype(str)
        df_bud["budget"] = df_bud["budget"].astype(float)

    # ---------- Année active ----------
    annees = sorted(df_bud["annee"].unique()) if not df_bud.empty else [2025]
    annee_active = st.selectbox("Année budgétaire", annees)

    tabs = st.tabs(["📊 Consulter", "➕ Ajouter", "✏️ Modifier", "🗑 Supprimer"])

    # ==================================================
    # 📊 CONSULTER
    # ==================================================
    with tabs[0]:
        df_view = df_bud[df_bud["annee"] == annee_active] if not df_bud.empty else pd.DataFrame()

        if df_view.empty:
            st.info("Aucun budget pour cette année.")
        else:
            col1, col2 = st.columns(2)

            with col1:
                compte_filtre = st.selectbox(
                    "Compte",
                    ["Tous"] + sorted(df_view["compte"].unique()),
                )

            if compte_filtre != "Tous":
                df_view = df_view[df_view["compte"] == compte_filtre]

            k1, k2, k3 = st.columns(3)
            k1.metric("Budget total (€)", f"{df_view['budget'].sum():,.2f}")
            k2.metric("Nombre de comptes", df_view["compte"].nunique())
            k3.metric("Budget moyen (€)", f"{df_view['budget'].mean():,.2f}")

            st.dataframe(
                df_view.sort_values("compte"),
                use_container_width=True,
            )

    # ==================================================
    # ➕ AJOUTER (SANS CASSER)
    # ==================================================
    with tabs[1]:
        with st.form("add_budget"):
            compte = st.text_input("Compte")
            budget = st.number_input("Budget (€)", min_value=0.0, step=10.0)
            submit = st.form_submit_button("Enregistrer")

        if submit:
            if compte:
                supabase.table("budgets").upsert(
                    {
                        "annee": int(annee_active),
                        "compte": str(compte),
                        "budget": float(budget),
                    },
                    on_conflict="annee,compte",
                ).execute()

                st.success("Budget enregistré.")
                st.rerun()
            else:
                st.error("Le compte est obligatoire.")

    # ==================================================
    # ✏️ MODIFIER
    # ==================================================
    with tabs[2]:
        df_mod = df_bud[df_bud["annee"] == annee_active]

        if df_mod.empty:
            st.info("Aucun budget à modifier.")
        else:
            compte_sel = st.selectbox("Compte", df_mod["compte"].tolist())
            ligne = df_mod[df_mod["compte"] == compte_sel].iloc[0]

            new_budget = st.number_input(
                "Nouveau budget (€)",
                value=float(ligne["budget"]),
                min_value=0.0,
                step=10.0,
            )

            if st.button("Mettre à jour"):
                supabase.table("budgets").update(
                    {"budget": float(new_budget)}
                ).eq("id", ligne["id"]).execute()

                st.success("Budget modifié.")
                st.rerun()

    # ==================================================
    # 🗑 SUPPRIMER
    # ==================================================
    with tabs[3]:
        df_del = df_bud[df_bud["annee"] == annee_active]

        if df_del.empty:
            st.info("Aucun budget à supprimer.")
        else:
            compte_sel = st.selectbox("Compte à supprimer", df_del["compte"].tolist())
            ligne = df_del[df_del["compte"] == compte_sel].iloc[0]

            st.warning(f"Suppression définitive du budget {compte_sel} ({annee_active})")

            if st.button("Confirmer la suppression"):
                supabase.table("budgets").delete().eq("id", ligne["id"]).execute()
                st.success("Budget supprimé.")
                st.rerun()

# ======================================================
# 📊 BUDGET VS RÉEL — STABLE
# ======================================================
if page == "📊 Budget vs Réel":

    st.header("📊 Budget vs Réel")

    dep_data = supabase.table("depenses").select("*").execute().data or []
    bud_data = supabase.table("budgets").select("*").execute().data or []

    df_dep = pd.DataFrame(dep_data)
    df_bud = pd.DataFrame(bud_data)

    if df_dep.empty or df_bud.empty:
        st.info("Données insuffisantes.")
    else:
        df_dep["annee"] = df_dep["annee"].astype(int)
        df_dep["compte"] = df_dep["compte"].astype(str)
        df_dep["montant_ttc"] = df_dep["montant_ttc"].astype(float)

        df_bud["annee"] = df_bud["annee"].astype(int)
        df_bud["compte"] = df_bud["compte"].astype(str)
        df_bud["budget"] = df_bud["budget"].astype(float)

        annee = st.selectbox("Année", sorted(df_bud["annee"].unique()))

        dep_agg = (
            df_dep[df_dep["annee"] == annee]
            .groupby("compte", as_index=False)["montant_ttc"]
            .sum()
            .rename(columns={"montant_ttc": "réel"})
        )

        bud_agg = (
            df_bud[df_bud["annee"] == annee]
            .groupby("compte", as_index=False)["budget"]
            .sum()
        )

        df_comp = pd.merge(bud_agg, dep_agg, on="compte", how="left").fillna(0)
        df_comp["écart (€)"] = df_comp["budget"] - df_comp["réel"]
        df_comp["écart (%)"] = (
            (df_comp["réel"] / df_comp["budget"])
            .replace([float("inf"), -float("inf")], 0)
            * 100
        )

        k1, k2, k3 = st.columns(3)
        k1.metric("Budget total", f"{df_comp['budget'].sum():,.2f} €")
        k2.metric("Dépenses réelles", f"{df_comp['réel'].sum():,.2f} €")
        k3.metric("Écart global", f"{df_comp['écart (€)'].sum():,.2f} €")

        st.dataframe(df_comp.sort_values("compte"), use_container_width=True)
