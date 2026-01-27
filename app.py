import streamlit as st
import pandas as pd
from supabase import create_client

# =========================
# CONFIG
# =========================
BASE_TANTIEMES = 10_000

st.set_page_config(
    page_title="Pilotage des charges",
    layout="wide"
)

# =========================
# OUTILS
# =========================
def euro(x):
    try:
        return f"{x:,.2f} €".replace(",", " ").replace(".", ",")
    except Exception:
        return "0,00 €"

@st.cache_resource
def get_supabase():
    return create_client(
        st.secrets["SUPABASE_URL"],
        st.secrets["SUPABASE_ANON_KEY"]
    )

def load_table(name, filters=None):
    q = supabase.table(name).select("*")
    if filters:
        for k, v in filters.items():
            q = q.eq(k, v)
    res = q.execute()
    return pd.DataFrame(res.data) if res.data else pd.DataFrame()

# =========================
# APP
# =========================
supabase = get_supabase()

st.sidebar.title("Navigation")
page = st.sidebar.radio(
    "Aller à",
    [
        "📄 État des dépenses",
        "💰 Budget",
        "📊 Budget vs Réel",
        "📈 Statistiques",
        "🚨 Contrôle de répartition",
    ]
)

annee = st.sidebar.selectbox("Année", [2023, 2024, 2025, 2026], index=2)

# =========================================================
# 📄 ÉTAT DES DÉPENSES
# =========================================================
if page == "📄 État des dépenses":
    st.title("📄 État des dépenses")

    df = load_table("depenses", {"annee": annee})

    if df.empty:
        st.info("Aucune dépense pour cette année")
    else:
        df["facture"] = df["facture_url"].apply(
            lambda x: f"[Ouvrir]({x})" if pd.notna(x) else ""
        )

        st.dataframe(
            df[[
                "date",
                "poste",
                "compte",
                "intitule_compte",
                "fournisseur",
                "montant_ttc",
                "commentaire",
                "facture"
            ]],
            use_container_width=True
        )

    st.markdown("### ➕ Ajouter une dépense")
    with st.form("add_depense"):
        date = st.date_input("Date")
        poste = st.text_input("Poste")
        compte = st.text_input("Compte")
        intitule = st.text_input("Intitulé du compte")
        fournisseur = st.text_input("Fournisseur")
        montant = st.number_input("Montant TTC", value=0.0)
        commentaire = st.text_area("Commentaire")
        facture_url = st.text_input("Lien facture (optionnel)")
        submit = st.form_submit_button("Enregistrer")

        if submit:
            supabase.table("depenses").insert({
                "date": str(date),
                "annee": annee,
                "poste": poste,
                "compte": compte,
                "intitule_compte": intitule,
                "fournisseur": fournisseur,
                "montant_ttc": montant,
                "commentaire": commentaire,
                "facture_url": facture_url
            }).execute()
            st.success("Dépense enregistrée")
            st.rerun()

# =========================================================
# 💰 BUDGET
# =========================================================
elif page == "💰 Budget":
    st.title("💰 Budget")

    df = load_table("budgets", {"annee": annee})

    if not df.empty:
        st.metric("Budget total", euro(df["budget"].sum()))
        st.dataframe(df[["poste", "budget"]], use_container_width=True)

    st.markdown("### ➕ Ajouter / modifier un poste budgétaire")
    with st.form("add_budget"):
        poste = st.text_input("Poste")
        budget = st.number_input("Budget annuel", value=0.0)
        submit = st.form_submit_button("Enregistrer")

        if submit:
            supabase.table("budgets").insert({
                "annee": annee,
                "poste": poste,
                "budget": budget
            }).execute()
            st.success("Budget enregistré")
            st.rerun()

# =========================================================
# 📊 BUDGET VS RÉEL (DÉTAILLÉ)
# =========================================================
elif page == "📊 Budget vs Réel":
    st.title("📊 Budget vs Réel")

    df_dep = load_table("depenses", {"annee": annee})
    df_bud = load_table("budgets", {"annee": annee})

    if df_dep.empty and df_bud.empty:
        st.warning("Aucune donnée")
        st.stop()

    dep = (
        df_dep
        .groupby("poste", as_index=False)
        .agg(reel=("montant_ttc", "sum"))
    )

    bud = (
        df_bud
        .groupby("poste", as_index=False)
        .agg(budget=("budget", "sum"))
    )

    df = bud.merge(dep, on="poste", how="outer").fillna(0)
    df["ecart"] = df["budget"] - df["reel"]
    df["ecart_pct"] = df.apply(
        lambda r: (r["ecart"] / r["budget"] * 100) if r["budget"] != 0 else 0,
        axis=1
    )

    c1, c2, c3 = st.columns(3)
    c1.metric("Budget", euro(df["budget"].sum()))
    c2.metric("Réel", euro(df["reel"].sum()))
    c3.metric("Écart", euro(df["ecart"].sum()))

    st.dataframe(
        df.rename(columns={
            "poste": "Poste",
            "budget": "Budget (€)",
            "reel": "Réel (€)",
            "ecart": "Écart (€)",
            "ecart_pct": "Écart (%)"
        }),
        use_container_width=True
    )

# =========================================================
# 📈 STATISTIQUES
# =========================================================
elif page == "📈 Statistiques":
    st.title("📈 Statistiques")

    df = load_table("depenses", {"annee": annee})
    if df.empty:
        st.info("Aucune donnée")
    else:
        c1, c2, c3 = st.columns(3)
        c1.metric("Total dépenses", euro(df["montant_ttc"].sum()))
        c2.metric("Nb factures", len(df))
        c3.metric("Dépense moyenne", euro(df["montant_ttc"].mean()))

        st.markdown("### Dépenses par poste")
        st.dataframe(
            df.groupby("poste", as_index=False)
            .agg(total=("montant_ttc", "sum")),
            use_container_width=True
        )

# =========================================================
# 🚨 CONTRÔLE DE RÉPARTITION
# =========================================================
elif page == "🚨 Contrôle de répartition":
    st.title("🚨 Contrôle de répartition")

    df_dep = load_table("depenses", {"annee": annee})
    df_rep = load_table("repartition_depenses")
    df_lots = load_table("lots")

    if df_dep.empty or df_rep.empty:
        st.warning("Données insuffisantes")
        st.stop()

    df = (
        df_rep
        .merge(df_dep, left_on="depense_id", right_on="id")
        .merge(df_lots, left_on="lot_id", right_on="id", suffixes=("", "_lot"))
    )

    df["montant_reparti"] = df["montant_ttc"] * df["quote_part"] / BASE_TANTIEMES

    ctrl = (
        df.groupby("depense_id", as_index=False)
        .agg(
            montant_depense=("montant_ttc", "first"),
            montant_reparti=("montant_reparti", "sum")
        )
    )

    ctrl["ecart"] = ctrl["montant_depense"] - ctrl["montant_reparti"]

    anomalies = ctrl[ctrl["ecart"].abs() > 0.01]

    if anomalies.empty:
        st.success("Toutes les dépenses sont correctement réparties")
    else:
        st.error(f"{len(anomalies)} anomalies détectées")
        st.dataframe(anomalies, use_container_width=True)