import streamlit as st
import pandas as pd
import unicodedata
from pathlib import Path
from utils.supabase_client import get_supabase
from utils.budget_ui import budget_ui

supabase = get_supabase()

from utils.supabase_client import get_supabase

supabase = get_supabase()

res = supabase.table("budgets").select("*").limit(5).execute()
st.write("Budgets:", res.data)

st.stop()
from utils.supabase_client import get_supabase

supabase = get_supabase()

test = supabase.table("budgets").select("*").limit(1).execute()
st.write("Connexion Supabase OK", test.data)


# ======================================================
# CONFIG
# ======================================================
st.set_page_config(page_title="Pilotage des charges", layout="wide")
st.title("Pilotage des charges de l’immeuble")

DATA_DIR = Path("data")
DEP_FILE = DATA_DIR / "base_depenses_immeuble.csv"
BUD_FILE = DATA_DIR / "budget_comptes_generaux.csv"

# ======================================================
# OUTILS
# ======================================================
def clean_columns(df):
    def norm(c):
        c = str(c).strip().lower()
        c = unicodedata.normalize("NFKD", c).encode("ascii", "ignore").decode()
        return c.replace(" ", "_").replace("-", "_")
    df.columns = [norm(c) for c in df.columns]
    return df


def groupe_compte(compte):
    compte = str(compte)
    return compte[:4] if compte.startswith(("621", "622")) else compte[:3]


def facture_cell(row):
    if row["pdf_url"]:
        return f'{row["piece_id"]} – <a href="{row["pdf_url"]}" target="_blank">📄 Ouvrir</a>'
    return row["piece_id"] or "—"


# ======================================================
# NORMALISATION
# ======================================================
def normalize_depenses(df):
    df = clean_columns(df)
    for col in ["poste", "fournisseur", "piece_id", "pdf_url"]:
        if col not in df.columns:
            df[col] = ""

    df["annee"] = df["annee"].astype(int)
    df["compte"] = df["compte"].astype(str)
    df["montant_ttc"] = df["montant_ttc"].astype(float)
    df["pdf_url"] = df["pdf_url"].astype(str)
    df["groupe_compte"] = df["compte"].apply(groupe_compte)
    return df


def normalize_budget(df):
    df = clean_columns(df)
    df["annee"] = df["annee"].astype(int)
    df["compte"] = df["compte"].astype(str)
    df["budget"] = df["budget"].astype(float)
    df["groupe_compte"] = df["compte"]
    return df


# ======================================================
# CHARGEMENT
# ======================================================
@st.cache_data(show_spinner=False)
def load_data():
    dep = normalize_depenses(pd.read_csv(DEP_FILE, encoding="utf-8-sig"))
    bud = normalize_budget(pd.read_csv(BUD_FILE, encoding="utf-8-sig"))
    return dep, bud


df_dep, df_bud = load_data()

# ======================================================
# SIDEBAR
# ======================================================
with st.sidebar:
    if st.button("🔄 Recharger les données"):
        st.cache_data.clear()
        st.rerun()

    page = st.radio(
        "Navigation",
        ["💰 Budget", "📊 Budget vs Réel", "🔍 Analyse détaillée"]
    )

# ======================================================
# 💰 BUDGET
# ======================================================
if page == "💰 Budget":

    annee = st.selectbox("Année budgétaire", sorted(df_bud["annee"].unique()))
    df_b = df_bud[df_bud["annee"] == annee].copy()

    st.metric(
        "Budget total (€)",
        f"{df_b['budget'].sum():,.0f}".replace(",", " ")
    )

    st.markdown("### ✏️ Édition du budget")
    df_edit = st.data_editor(
        df_b,
        num_rows="dynamic",
        use_container_width=True
    )

    st.download_button(
        "📥 Télécharger budget_comptes_generaux.csv",
        df_edit.to_csv(index=False).encode("utf-8"),
        file_name="budget_comptes_generaux.csv"
    )

    st.info(
        "Les modifications sont temporaires.\n"
        "➡️ Télécharge le CSV et commit-le dans GitHub pour les rendre officielles."
    )

# ======================================================
# 📊 BUDGET VS RÉEL
# ======================================================
if page == "📊 Budget vs Réel":

    annee = st.selectbox("Année", sorted(df_dep["annee"].unique()))

    dep = df_dep[df_dep["annee"] == annee]
    bud = df_bud[df_bud["annee"] == annee]

    reel = dep.groupby("groupe_compte")["montant_ttc"].sum().reset_index()
    comp = bud.merge(reel, on="groupe_compte", how="left").fillna(0)

    comp["Écart (€)"] = comp["montant_ttc"] - comp["budget"]
    comp["Écart (%)"] = (comp["Écart (€)"] / comp["budget"] * 100).round(1)
    comp["Statut"] = comp["Écart (€)"].apply(lambda x: "DÉPASSEMENT" if x > 0 else "OK")

    # KPI
    k1, k2, k3, k4, k5 = st.columns(5)
    k1.metric("Budget total (€)", f"{comp['budget'].sum():,.0f}".replace(",", " "))
    k2.metric("Réel net (€)", f"{comp['montant_ttc'].sum():,.0f}".replace(",", " "))
    k3.metric("Écart total (€)", f"{comp['Écart (€)'].sum():,.0f}".replace(",", " "))
    k4.metric("Écart moyen (%)", f"{comp['Écart (%)'].mean():.1f} %")
    k5.metric("Comptes en dépassement", int((comp["Écart (€)"] > 0).sum()))

    st.dataframe(
        comp[
            ["groupe_compte", "budget", "montant_ttc", "Écart (€)", "Écart (%)", "Statut"]
        ],
        use_container_width=True
    )

# ======================================================
# 🔍 ANALYSE DÉTAILLÉE
# ======================================================
if page == "🔍 Analyse détaillée":

    f1, f2, f3, f4 = st.columns(4)

    with f1:
        annee = st.selectbox("Année", sorted(df_dep["annee"].unique()))

    with f2:
        groupes = ["Tous"] + sorted(df_dep["groupe_compte"].unique())
        grp = st.selectbox("Groupe de comptes", groupes)

    df_f = df_dep[df_dep["annee"] == annee]

    if grp != "Tous":
        df_f = df_f[df_f["groupe_compte"] == grp]

    with f3:
        comptes = ["Tous"] + sorted(df_f["compte"].unique())
        cpt = st.selectbox("Compte", comptes)

    if cpt != "Tous":
        df_f = df_f[df_f["compte"] == cpt]

    with f4:
        fournisseurs = ["Tous"] + sorted(df_f["fournisseur"].unique())
        four = st.selectbox("Fournisseur", fournisseurs)

    if four != "Tous":
        df_f = df_f[df_f["fournisseur"] == four]

    dep_pos = df_f[df_f["montant_ttc"] > 0]["montant_ttc"].sum()
    dep_neg = df_f[df_f["montant_ttc"] < 0]["montant_ttc"].sum()
    net = dep_pos + dep_neg

elif page == "💰 Budget":
    budget_ui(supabase)

    k1, k2, k3, k4 = st.columns(4)
    k1.metric("Dépenses brutes (€)", f"{dep_pos:,.0f}".replace(",", " "))
    k2.metric("Avoirs (€)", f"{dep_neg:,.0f}".replace(",", " "))
    k3.metric("Dépenses nettes (€)", f"{net:,.0f}".replace(",", " "))
    k4.metric("Nombre de lignes", len(df_f))

    df_f["Facture"] = df_f.apply(facture_cell, axis=1)

    st.markdown(
        df_f[
            ["compte", "poste", "fournisseur", "montant_ttc", "Facture"]
        ].to_html(escape=False, index=False),
        unsafe_allow_html=True
    )
