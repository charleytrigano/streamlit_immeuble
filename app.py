import streamlit as st
import pandas as pd

from utils.supabase_client import get_supabase
from utils.depenses_repo import load_depenses, insert_depense, delete_depense
from utils.budgets_repo import load_budgets, upsert_budgets, delete_budget
from utils.budget_vs_reel_repo import compute_budget_vs_reel

# ======================
# CONFIG
# ======================
st.set_page_config(
    page_title="Pilotage des charges de l’immeuble",
    layout="wide",
)

supabase = get_supabase()

# ======================
# SIDEBAR
# ======================
st.sidebar.title("📊 Navigation")

page = st.sidebar.radio(
    "Aller à",
    [
        "📈 État des dépenses",
        "💰 Budget",
        "📊 Budget vs Réel",
    ],
)

ANNEES = list(range(2020, 2031))
ANNEE_DEFAUT = ANNEES.index(2025)

# =========================================================
# 📈 ÉTAT DES DÉPENSES
# =========================================================
if page == "📈 État des dépenses":
    st.title("📈 État des dépenses")

    tabs = st.tabs(["📊 Consulter", "➕ Ajouter", "🗑 Supprimer"])

    # ---------- CONSULTER ----------
    with tabs[0]:
        annee = st.selectbox("Année", ANNEES, index=ANNEE_DEFAUT)

        df = load_depenses(supabase, annee)

        if df.empty:
            st.warning("Aucune dépense pour cette année.")
        else:
            col1, col2, col3 = st.columns(3)
            col1.metric("Total dépenses (€)", f"{df['montant_ttc'].sum():,.2f}")
            col2.metric("Nombre de lignes", len(df))
            col3.metric("Moyenne (€)", f"{df['montant_ttc'].mean():,.2f}")

            fournisseurs = ["Tous"] + sorted(df["fournisseur"].dropna().unique())
            fournisseur = st.selectbox("Fournisseur", fournisseurs)

            if fournisseur != "Tous":
                df = df[df["fournisseur"] == fournisseur]

            st.dataframe(df, use_container_width=True)

    # ---------- AJOUTER ----------
    with tabs[1]:
        st.subheader("➕ Ajouter une dépense")

        with st.form("add_depense"):
            annee = st.selectbox("Année", ANNEES, index=ANNEE_DEFAUT)
            date = st.date_input("Date")
            compte = st.text_input("Compte")
            poste = st.text_input("Poste")
            fournisseur = st.text_input("Fournisseur")
            montant = st.number_input("Montant TTC", step=0.01)
            piece_id = st.text_input("Pièce ID")
            pdf_url = st.text_input("Lien PDF (Google Drive)")

            submitted = st.form_submit_button("Enregistrer")

            if submitted:
                insert_depense(
                    supabase,
                    {
                        "annee": annee,
                        "date": date.isoformat(),
                        "compte": compte,
                        "poste": poste,
                        "fournisseur": fournisseur,
                        "montant_ttc": montant,
                        "piece_id": piece_id,
                        "pdf_url": pdf_url,
                    },
                )
                st.success("Dépense ajoutée")
                st.rerun()

    # ---------- SUPPRIMER ----------
    with tabs[2]:
        st.subheader("🗑 Supprimer une dépense")

        annee = st.selectbox("Année", ANNEES, index=ANNEE_DEFAUT, key="del_dep_annee")
        df = load_depenses(supabase, annee)

        if not df.empty:
            dep_id = st.selectbox(
                "Sélectionner une dépense",
                df["id"],
                format_func=lambda x: f"{x}",
            )

            if st.button("Supprimer définitivement"):
                delete_depense(supabase, dep_id)
                st.success("Dépense supprimée")
                st.rerun()

# =========================================================
# 💰 BUDGET
# =========================================================
elif page == "💰 Budget":
    st.title("💰 Budget annuel")

    tabs = st.tabs(["📊 Consulter", "➕ Ajouter / Modifier", "🗑 Supprimer"])

    # ---------- CONSULTER ----------
    with tabs[0]:
        annee = st.selectbox("Année budgétaire", ANNEES, index=ANNEE_DEFAUT)
        df = load_budgets(supabase, annee)

        if df.empty:
            st.warning("Aucun budget pour cette année.")
        else:
            st.metric("Budget total (€)", f"{df['budget'].sum():,.2f}")
            st.dataframe(df, use_container_width=True)

    # ---------- AJOUTER / MODIFIER ----------
    with tabs[1]:
        annee = st.selectbox("Année", ANNEES, index=ANNEE_DEFAUT, key="edit_budget")

        df = load_budgets(supabase, annee)
        if df.empty:
            df = pd.DataFrame(columns=["compte", "budget", "groupe_compte"])

        edited = st.data_editor(
            df,
            num_rows="dynamic",
            use_container_width=True,
        )

        if st.button("💾 Enregistrer le budget"):
            edited["annee"] = annee
            upsert_budgets(supabase, edited)
            st.success("Budget enregistré")
            st.rerun()

    # ---------- SUPPRIMER ----------
    with tabs[2]:
        annee = st.selectbox("Année", ANNEES, index=ANNEE_DEFAUT, key="del_budget")
        df = load_budgets(supabase, annee)

        if not df.empty:
            compte = st.selectbox("Compte", df["compte"])

            if st.button("Supprimer ce compte"):
                delete_budget(supabase, annee, compte)
                st.success("Budget supprimé")
                st.rerun()

# =========================================================
# 📊 BUDGET VS RÉEL
# =========================================================
elif page == "📊 Budget vs Réel":
    st.title("📊 Budget vs Réel")

    annee = st.selectbox("Année", ANNEES, index=ANNEE_DEFAUT)

    df_dep = load_depenses(supabase, annee)
    df_bud = load_budgets(supabase, annee)

    if df_dep.empty or df_bud.empty:
        st.warning("Données insuffisantes pour cette année.")
    else:
        df = compute_budget_vs_reel(df_bud, df_dep)

        col1, col2 = st.columns(2)
        col1.metric("Budget total (€)", f"{df['budget'].sum():,.2f}")
        col2.metric("Réel total (€)", f"{df['reel'].sum():,.2f}")

        st.dataframe(df, use_container_width=True)