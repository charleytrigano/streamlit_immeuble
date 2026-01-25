import streamlit as st
import pandas as pd
from supabase import create_client

# ======================================================
# CONFIG
# ======================================================
st.set_page_config(
    page_title="🏢 Pilotage des charges",
    layout="wide"
)

# ======================================================
# SUPABASE
# ======================================================
@st.cache_resource
def get_supabase():
    return create_client(
        st.secrets["SUPABASE_URL"],
        st.secrets["SUPABASE_ANON_KEY"]
    )

supabase = get_supabase()

# ======================================================
# OUTILS
# ======================================================
def euro(x):
    return f"{x:,.2f} €".replace(",", " ").replace(".", ",")

def safe_execute(query, label):
    try:
        return query.execute()
    except Exception as e:
        st.error(f"❌ Erreur Supabase : {label}")
        st.exception(e)
        st.stop()

# ======================================================
# SIDEBAR
# ======================================================
st.sidebar.title("Navigation")

page = st.sidebar.radio(
    "Aller à",
    [
        "📋 État des dépenses",
        "💰 Budget",
        "📊 Budget vs Réel",
        "📈 Statistiques",
        "✅ Contrôle répartition",
    ]
)

# ======================================================
# 📋 ÉTAT DES DÉPENSES
# ======================================================
if page == "📋 État des dépenses":
    st.title("📋 État des dépenses")

    annee = st.selectbox("Année", [2023, 2024, 2025, 2026], index=2)

    dep_resp = safe_execute(
        supabase.table("depenses").select("*").eq("annee", annee),
        "depenses"
    )

    df = pd.DataFrame(dep_resp.data)

    if df.empty:
        st.info("Aucune dépense.")
    else:
        # KPI
        col1, col2, col3 = st.columns(3)
        col1.metric("Total", euro(df["montant_ttc"].sum()))
        col2.metric("Lignes", len(df))
        col3.metric("Moyenne", euro(df["montant_ttc"].mean()))

        st.dataframe(df, use_container_width=True)

    st.divider()

    st.subheader("➕ Ajouter une dépense")

    with st.form("add_depense"):
        d = st.date_input("Date")
        compte = st.text_input("Compte")
        poste = st.text_input("Poste")
        fournisseur = st.text_input("Fournisseur")
        montant = st.number_input("Montant TTC", value=0.0)
        lien = st.text_input("Lien facture (optionnel)")
        submitted = st.form_submit_button("Enregistrer")

        if submitted:
            payload = {
                "annee": d.year,
                "date": str(d),
                "compte": compte,
                "poste": poste,
                "fournisseur": fournisseur,
                "montant_ttc": montant,
                "pdf_url": lien or None,
            }
            safe_execute(
                supabase.table("depenses").insert(payload),
                "insert depense"
            )
            st.success("Dépense enregistrée")
            st.rerun()

# ======================================================
# 💰 BUDGET
# ======================================================
elif page == "💰 Budget":
    st.title("💰 Budget")

    annee = st.selectbox("Année budgétaire", [2023, 2024, 2025, 2026])

    bud_resp = safe_execute(
        supabase.table("budgets").select("*").eq("annee", annee),
        "budgets"
    )

    dfb = pd.DataFrame(bud_resp.data)

    if dfb.empty:
        st.warning("Aucun budget pour cette année.")
    else:
        st.metric("Budget total", euro(dfb["budget"].sum()))
        st.dataframe(dfb, use_container_width=True)

# ======================================================
# 📊 BUDGET VS RÉEL
# ======================================================
elif page == "📊 Budget vs Réel":
    st.title("📊 Budget vs Réel")

    annee = st.selectbox("Année", [2023, 2024, 2025, 2026])

    dep = safe_execute(
        supabase.table("depenses").select("compte,montant_ttc").eq("annee", annee),
        "depenses"
    )
    bud = safe_execute(
        supabase.table("budgets").select("groupe_compte,budget").eq("annee", annee),
        "budgets"
    )

    df_dep = pd.DataFrame(dep.data)
    df_bud = pd.DataFrame(bud.data)

    if df_dep.empty or df_bud.empty:
        st.warning("Données insuffisantes.")
        st.stop()

    def grp(c):
        return c[:4] if c in {"6211","6213","6222","6223"} else c[:3]

    df_dep["groupe"] = df_dep["compte"].astype(str).apply(grp)
    df_dep = df_dep.groupby("groupe", as_index=False)["montant_ttc"].sum()

    df = df_bud.merge(
        df_dep,
        left_on="groupe_compte",
        right_on="groupe",
        how="left"
    ).fillna(0)

    df["écart"] = df["budget"] - df["montant_ttc"]

    st.dataframe(
        df.rename(columns={
            "groupe_compte": "Compte",
            "budget": "Budget",
            "montant_ttc": "Réel",
            "écart": "Écart"
        }),
        use_container_width=True
    )

# ======================================================
# 📈 STATISTIQUES
# ======================================================
elif page == "📈 Statistiques":
    st.title("📈 Statistiques")

    dep = safe_execute(
        supabase.table("depenses").select("*"),
        "depenses"
    )

    df = pd.DataFrame(dep.data)
    if df.empty:
        st.info("Aucune donnée.")
        st.stop()

    col1, col2, col3 = st.columns(3)
    col1.metric("Total", euro(df["montant_ttc"].sum()))
    col2.metric("Dépenses", len(df))
    col3.metric("Années", df["annee"].nunique())

    st.dataframe(df, use_container_width=True)

# ======================================================
# ✅ CONTRÔLE RÉPARTITION
# ======================================================
elif page == "✅ Contrôle répartition":
    st.title("✅ Contrôle de répartition")

    annee = st.selectbox("Année", [2023, 2024, 2025, 2026])

    dep = safe_execute(
        supabase.table("depenses").select("id,montant_ttc").eq("annee", annee),
        "depenses"
    )
    rep = safe_execute(
        supabase.table("repartition_depenses").select("depense_id,quote_part"),
        "repartition_depenses"
    )

    df_dep = pd.DataFrame(dep.data)
    df_rep = pd.DataFrame(rep.data)

    if df_dep.empty:
        st.info("Aucune dépense.")
        st.stop()

    df = df_rep.merge(df_dep, left_on="depense_id", right_on="id", how="left")
    df["reparti"] = df["montant_ttc"] * df["quote_part"]

    ctrl = df.groupby("depense_id", as_index=False).agg(
        montant=("montant_ttc","first"),
        reparti=("reparti","sum")
    )

    ctrl["écart"] = ctrl["montant"] - ctrl["reparti"]

    st.dataframe(ctrl, use_container_width=True)