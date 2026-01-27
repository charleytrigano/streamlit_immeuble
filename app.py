import streamlit as st
import pandas as pd
from supabase import create_client

# =========================
# CONFIG
# =========================
st.set_page_config("Pilotage des charges", layout="wide")

@st.cache_resource
def get_supabase():
    return create_client(
        st.secrets["SUPABASE_URL"],
        st.secrets["SUPABASE_ANON_KEY"]
    )

supabase = get_supabase()

def euro(v):
    return f"{v:,.2f} €".replace(",", " ").replace(".", ",")

# =========================
# LOADERS
# =========================
def load_depenses():
    return pd.DataFrame(
        supabase.table("depenses")
        .select("*")
        .execute()
        .data
    )

def load_plan():
    return pd.DataFrame(
        supabase.table("plan_comptable")
        .select("*")
        .eq("actif", True)
        .execute()
        .data
    )

def load_budgets():
    return pd.DataFrame(
        supabase.table("budgets")
        .select("*")
        .execute()
        .data
    )

# =========================
# UI
# =========================
st.title("🏢 Pilotage des charges")

tabs = st.tabs([
    "📄 État des dépenses",
    "🧾 Plan comptable",
    "💰 Budget"
])

# ======================================================
# 📄 ÉTAT DES DÉPENSES
# ======================================================
with tabs[0]:
    df_dep = load_depenses()
    df_plan = load_plan()
    df_bud = load_budgets()

    df = df_dep.merge(df_plan, on="compte", how="left")

    st.subheader("🔎 Filtres")

    colf1, colf2, colf3, colf4 = st.columns(4)

    annee = colf1.selectbox(
        "Année",
        sorted(df["annee"].unique())
    )

    compte = colf2.selectbox(
        "Compte",
        ["Tous"] + sorted(df["compte"].unique())
    )

    fournisseur = colf3.selectbox(
        "Fournisseur",
        ["Tous"] + sorted(df["fournisseur"].dropna().unique())
    )

    groupe = colf4.selectbox(
        "Groupe de compte",
        ["Tous"] + sorted(df["groupe_compte"].dropna().unique())
    )

    df = df[df["annee"] == annee]

    if compte != "Tous":
        df = df[df["compte"] == compte]

    if fournisseur != "Tous":
        df = df[df["fournisseur"] == fournisseur]

    if groupe != "Tous":
        df = df[df["groupe_compte"] == groupe]

    # ================= KPI =================
    total_dep = df["montant_ttc"].sum()

    bud_annee = df_bud[df_bud["annee"] == annee]["budget"].sum()
    ecart = total_dep - bud_annee

    k1, k2, k3 = st.columns(3)
    k1.metric("Total dépenses", euro(total_dep))
    k2.metric("Budget", euro(bud_annee))
    k3.metric("Écart", euro(ecart))

    # ================= TABLE =================
    df["facture"] = df["facture_path"].apply(
        lambda x: f"[📎 Ouvrir]({x})" if pd.notna(x) else ""
    )

    st.dataframe(
        df[[
            "date",
            "compte",
            "libelle_compte",
            "groupe_compte",
            "fournisseur",
            "montant_ttc",
            "commentaire",
            "facture"
        ]],
        use_container_width=True
    )

# ======================================================
# 🧾 PLAN COMPTABLE
# ======================================================
with tabs[1]:
    st.subheader("Plan comptable")

    df_plan = load_plan()
    st.dataframe(df_plan, use_container_width=True)

    with st.expander("➕ Ajouter / modifier un compte"):
        compte = st.text_input("Compte (8 chiffres)")
        lib = st.text_input("Libellé compte")
        grp = st.text_input("Groupe (3 chiffres)")
        lib_grp = st.text_input("Libellé groupe")

        if st.button("Enregistrer"):
            supabase.table("plan_comptable").upsert({
                "compte": compte,
                "libelle_compte": lib,
                "groupe_compte": grp,
                "libelle_groupe": lib_grp,
                "actif": True
            }).execute()
            st.success("Compte enregistré")

# ======================================================
# 💰 BUDGET
# ======================================================
with tabs[2]:
    st.subheader("Budgets")

    df_bud = load_budgets()
    st.dataframe(df_bud, use_container_width=True)

    with st.expander("➕ Ajouter / modifier un budget"):
        an = st.number_input("Année", step=1)
        grp = st.text_input("Groupe de compte")
        bud = st.number_input("Budget", step=100.0)

        if st.button("Enregistrer le budget"):
            supabase.table("budgets").upsert({
                "annee": an,
                "groupe_compte": grp,
                "budget": bud
            }).execute()
            st.success("Budget enregistré")