import streamlit as st
import pandas as pd
from supabase import create_client
from uuid import uuid4

# =========================
# CONFIG
# =========================
st.set_page_config(page_title="Pilotage des charges", layout="wide")

SUPABASE_URL = st.secrets["SUPABASE_URL"]
SUPABASE_KEY = st.secrets["SUPABASE_ANON_KEY"]
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# =========================
# HELPERS
# =========================
def euro(v):
    return f"{v:,.2f} €".replace(",", " ").replace(".", ",")

@st.cache_data
def load_depenses():
    res = supabase.table("depenses").select("*").execute()
    return pd.DataFrame(res.data)

@st.cache_data
def load_plan():
    res = supabase.table("plan_comptable").select("*").execute()
    return pd.DataFrame(res.data)

@st.cache_data
def load_budget():
    res = supabase.table("budgets").select("*").execute()
    return pd.DataFrame(res.data)

def refresh():
    st.cache_data.clear()

# =========================
# UI
# =========================
st.title("📊 Pilotage des charges")

tabs = st.tabs([
    "📄 État des dépenses",
    "🧾 Plan comptable",
    "💰 Budget"
])

# =========================================================
# 📄 ÉTAT DES DÉPENSES
# =========================================================
with tabs[0]:
    df = load_depenses()
    pc = load_plan()

    if df.empty:
        st.warning("Aucune dépense disponible")
        st.stop()

    df = df.merge(
        pc,
        how="left",
        left_on="compte",
        right_on="compte_8"
    )

    st.subheader("🔎 Filtres")

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        annee = st.selectbox("Année", sorted(df["annee"].unique()))

    with col2:
        compte = st.selectbox(
            "Compte",
            ["Tous"] + sorted(df["compte"].dropna().unique().tolist())
        )

    with col3:
        fournisseur = st.selectbox(
            "Fournisseur",
            ["Tous"] + sorted(df["fournisseur"].dropna().unique().tolist())
        )

    with col4:
        groupe = st.selectbox(
            "Groupe de compte",
            ["Tous"] + sorted(df["groupe_compte"].dropna().unique().tolist())
        )

    df_f = df[df["annee"] == annee]

    if compte != "Tous":
        df_f = df_f[df_f["compte"] == compte]

    if fournisseur != "Tous":
        df_f = df_f[df_f["fournisseur"] == fournisseur]

    if groupe != "Tous":
        df_f = df_f[df_f["groupe_compte"] == groupe]

    st.divider()

    col1, col2, col3 = st.columns(3)
    col1.metric("Total dépenses", euro(df_f["montant_ttc"].sum()))
    col2.metric("Nombre de lignes", len(df_f))
    col3.metric("Dépense moyenne", euro(df_f["montant_ttc"].mean()))

    st.divider()

    st.dataframe(
        df_f[[
            "date",
            "compte",
            "libelle",
            "groupe_compte",
            "libelle_groupe",
            "poste",
            "fournisseur",
            "montant_ttc",
            "facture_url"
        ]].sort_values("date", ascending=False),
        use_container_width=True
    )

# =========================================================
# 🧾 PLAN COMPTABLE
# =========================================================
with tabs[1]:
    st.subheader("🧾 Plan comptable")

    pc = load_plan()

    st.dataframe(pc, use_container_width=True)

    st.divider()
    st.subheader("➕ Ajouter / modifier un compte")

    with st.form("plan_form"):
        compte_8 = st.text_input("Compte (8 chiffres)")
        libelle = st.text_input("Libellé compte")
        groupe = st.text_input("Groupe de compte (ex: 601)")
        libelle_groupe = st.text_input("Libellé groupe")

        submitted = st.form_submit_button("Enregistrer")

        if submitted:
            supabase.table("plan_comptable").upsert({
                "compte_8": compte_8,
                "libelle": libelle,
                "groupe_compte": groupe,
                "libelle_groupe": libelle_groupe
            }).execute()
            refresh()
            st.success("Compte enregistré")

    st.divider()
    st.subheader("🗑 Supprimer un compte")

    compte_del = st.selectbox(
        "Compte à supprimer",
        pc["compte_8"].tolist()
    )

    if st.button("Supprimer"):
        supabase.table("plan_comptable") \
            .delete() \
            .eq("compte_8", compte_del) \
            .execute()
        refresh()
        st.success("Compte supprimé")

# =========================================================
# 💰 BUDGET
# =========================================================
with tabs[2]:
    st.subheader("💰 Budget par groupe de compte")

    df_b = load_budget()

    if not df_b.empty:
        st.dataframe(df_b, use_container_width=True)

    st.divider()
    st.subheader("➕ Ajouter / modifier budget")

    with st.form("budget_form"):
        annee = st.number_input("Année", min_value=2020, max_value=2100, value=2025)
        groupe = st.text_input("Groupe de compte")
        montant = st.number_input("Montant", min_value=0.0)

        submit = st.form_submit_button("Enregistrer")

        if submit:
            supabase.table("budgets").insert({
                "id": str(uuid4()),
                "annee": annee,
                "groupe_compte": groupe,
                "montant": montant
            }).execute()
            refresh()
            st.success("Budget enregistré")

    if not df_b.empty:
        st.divider()
        st.subheader("🗑 Supprimer un budget")

        id_del = st.selectbox(
            "Budget à supprimer",
            df_b["id"].tolist()
        )

        if st.button("Supprimer le budget"):
            supabase.table("budgets") \
                .delete() \
                .eq("id", id_del) \
                .execute()
            refresh()
            st.success("Budget supprimé")
