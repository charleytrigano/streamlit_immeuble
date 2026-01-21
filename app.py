import streamlit as st
import pandas as pd

from utils.supabase_client import get_supabase

# ======================================================
# CONFIG
# ======================================================
st.set_page_config(
    page_title="Pilotage des charges de l’immeuble",
    layout="wide",
)

st.title("Pilotage des charges de l’immeuble")

supabase = get_supabase()

ANNEES = list(range(2020, 2031))
ANNEE_DEFAUT = ANNEES.index(2025)

# ======================================================
# SIDEBAR
# ======================================================
page = st.sidebar.radio(
    "Navigation",
    ["📈 État des dépenses", "💰 Budget", "📊 Budget vs Réel"],
)

# ======================================================
# 📈 ÉTAT DES DÉPENSES
# ======================================================
if page == "📈 État des dépenses":

    tabs = st.tabs(["📊 Consulter", "➕ Ajouter", "🗑 Supprimer"])

    # ---------- CONSULTER ----------
    with tabs[0]:
        annee = st.selectbox("Année", ANNEES, index=ANNEE_DEFAUT)

        dep = (
            supabase
            .table("depenses")
            .select("*")
            .eq("annee", annee)
            .execute()
            .data
        )

        df = pd.DataFrame(dep)

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
        with st.form("add_depense"):
            annee = st.selectbox("Année", ANNEES, index=ANNEE_DEFAUT)
            date = st.date_input("Date")
            compte = st.text_input("Compte")
            poste = st.text_input("Poste")
            fournisseur = st.text_input("Fournisseur")
            montant = st.number_input("Montant TTC", step=0.01)
            piece_id = st.text_input("Pièce")
            pdf_url = st.text_input("Lien facture (Google Drive preview)")

            submit = st.form_submit_button("💾 Enregistrer")

        if submit:
            supabase.table("depenses").insert({
                "annee": int(annee),
                "date": date.isoformat(),
                "compte": compte,
                "poste": poste,
                "fournisseur": fournisseur,
                "montant_ttc": float(montant),
                "piece_id": piece_id,
                "pdf_url": pdf_url,
            }).execute()

            st.success("Dépense ajoutée")
            st.rerun()

    # ---------- SUPPRIMER ----------
    with tabs[2]:
        annee = st.selectbox("Année", ANNEES, index=ANNEE_DEFAUT, key="del_dep")
        dep = (
            supabase
            .table("depenses")
            .select("id, poste, montant_ttc")
            .eq("annee", annee)
            .execute()
            .data
        )

        df = pd.DataFrame(dep)

        if not df.empty:
            dep_id = st.selectbox(
                "Dépense",
                df["id"],
                format_func=lambda i: f"{df.loc[df['id']==i,'poste'].values[0]} – {df.loc[df['id']==i,'montant_ttc'].values[0]} €",
            )

            if st.button("❌ Supprimer définitivement"):
                supabase.table("depenses").delete().eq("id", dep_id).execute()
                st.success("Dépense supprimée")
                st.rerun()

# ======================================================
# 💰 BUDGET
# ======================================================
elif page == "💰 Budget":

    annee = st.selectbox("Année budgétaire", ANNEES, index=ANNEE_DEFAUT)

    tabs = st.tabs(["📊 Consulter", "➕ Ajouter", "✏️ Modifier", "🗑 Supprimer"])

    bud = (
        supabase
        .table("budgets")
        .select("*")
        .eq("annee", annee)
        .execute()
        .data
    )

    df = pd.DataFrame(bud)

    # ---------- CONSULTER ----------
    with tabs[0]:
        if df.empty:
            st.warning("Aucun budget pour cette année.")
        else:
            st.metric("Budget total (€)", f"{df['budget'].sum():,.2f}")
            st.dataframe(df, use_container_width=True)

    # ---------- AJOUTER ----------
    with tabs[1]:
        with st.form("add_budget"):
            compte = st.text_input("Compte")
            budget = st.number_input("Budget (€)", step=100.0)
            submit = st.form_submit_button("💾 Enregistrer")

        if submit:
            supabase.table("budgets").upsert(
                {
                    "annee": int(annee),
                    "compte": compte,
                    "budget": float(budget),
                },
                on_conflict="annee,compte",
            ).execute()

            st.success("Budget enregistré")
            st.rerun()

    # ---------- MODIFIER ----------
    with tabs[2]:
        if not df.empty:
            row_id = st.selectbox(
                "Poste",
                df["id"],
                format_func=lambda i: f"{df.loc[df['id']==i,'compte'].values[0]}",
            )

            row = df[df["id"] == row_id].iloc[0]

            new_budget = st.number_input(
                "Nouveau budget (€)",
                value=float(row["budget"]),
                step=100.0,
            )

            if st.button("💾 Enregistrer modification"):
                supabase.table("budgets") \
                    .update({"budget": float(new_budget)}) \
                    .eq("id", row_id) \
                    .execute()

                st.success("Budget modifié")
                st.rerun()

    # ---------- SUPPRIMER ----------
    with tabs[3]:
        if not df.empty:
            row_id = st.selectbox(
                "Budget",
                df["id"],
                format_func=lambda i: f"{df.loc[df['id']==i,'compte'].values[0]}",
            )

            if st.button("❌ Supprimer"):
                supabase.table("budgets").delete().eq("id", row_id).execute()
                st.success("Budget supprimé")
                st.rerun()

# ======================================================
# 📊 BUDGET VS RÉEL
# ======================================================
elif page == "📊 Budget vs Réel":

    annee = st.selectbox("Année", ANNEES, index=ANNEE_DEFAUT)

    dep = pd.DataFrame(
        supabase.table("depenses").select("*").eq("annee", annee).execute().data
    )
    bud = pd.DataFrame(
        supabase.table("budgets").select("*").eq("annee", annee).execute().data
    )

    if dep.empty or bud.empty:
        st.warning("Données insuffisantes.")
    else:
        dep["compte_budget"] = dep["compte"].str[:3]
        reel = dep.groupby("compte_budget")["montant_ttc"].sum().reset_index()
        comp = bud.merge(reel, left_on="compte", right_on="compte_budget", how="left")
        comp["montant_ttc"] = comp["montant_ttc"].fillna(0)
        comp["ecart"] = comp["montant_ttc"] - comp["budget"]
        comp["ecart_pct"] = comp["ecart"] / comp["budget"] * 100

        col1, col2 = st.columns(2)
        col1.metric("Budget total (€)", f"{comp['budget'].sum():,.2f}")
        col2.metric("Réel total (€)", f"{comp['montant_ttc'].sum():,.2f}")

        st.dataframe(comp, use_container_width=True)