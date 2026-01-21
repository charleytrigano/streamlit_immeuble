import streamlit as st
import pandas as pd
import unicodedata
from pathlib import Path

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
# CHARGEMENT OFFICIEL
# ======================================================
@st.cache_data(show_spinner=False)
def load_official_data():
    dep = normalize_depenses(pd.read_csv(DEP_FILE, encoding="utf-8-sig"))
    bud = normalize_budget(pd.read_csv(BUD_FILE, encoding="utf-8-sig"))
    return dep, bud


df_dep, df_bud = load_official_data()

# ======================================================
# SIDEBAR — RESTAURATION
# ======================================================
with st.sidebar:
    st.markdown("## 🔄 Données")

    if st.button("Recharger depuis GitHub"):
        st.cache_data.clear()
        st.rerun()

    st.markdown("### Restaurer depuis XLSX")
    xlsx = st.file_uploader("immeuble_data.xlsx", type="xlsx")

    if xlsx:
        xls = pd.ExcelFile(xlsx)
        if "depenses" in xls.sheet_names and "budget" in xls.sheet_names:
            df_dep = normalize_depenses(pd.read_excel(xls, "depenses"))
            df_bud = normalize_budget(pd.read_excel(xls, "budget"))
            st.success("XLSX chargé en mémoire (export CSV requis)")
        else:
            st.error("Onglets requis manquants")

    page = st.radio(
        "Navigation",
        ["📊 Budget vs Réel", "🔍 Analyse détaillée"]
    )

# ======================================================
# 📊 BUDGET VS RÉEL (ANALYSE AUTOMATIQUE)
# ======================================================
if page == "📊 Budget vs Réel":

    annee = st.selectbox("Année", sorted(df_dep["annee"].unique()))

    dep = df_dep[df_dep["annee"] == annee]
    bud = df_bud[df_bud["annee"] == annee]

    reel = dep.groupby("groupe_compte")["montant_ttc"].sum().reset_index()
    comp = bud.merge(reel, on="groupe_compte", how="left").fillna(0)

    comp["écart (€)"] = comp["montant_ttc"] - comp["budget"]
    comp["écart (%)"] = (comp["écart (€)"] / comp["budget"] * 100).round(1)
    comp["statut"] = comp["écart (€)"].apply(lambda x: "DÉPASSEMENT" if x > 0 else "OK")

    st.dataframe(comp, use_container_width=True)

    st.download_button(
        "Télécharger budget_comptes_generaux.csv",
        bud.to_csv(index=False).encode("utf-8"),
        file_name="budget_comptes_generaux.csv"
    )

# ======================================================
# 🔍 DRILL-DOWN — ÉCRITURES & FACTURES
# ======================================================
if page == "🔍 Analyse détaillée":

    annee = st.selectbox("Année", sorted(df_dep["annee"].unique()))
    groupes = sorted(df_dep["groupe_compte"].unique())
    grp = st.selectbox("Groupe de compte", groupes)

    df_f = df_dep[
        (df_dep["annee"] == annee) &
        (df_dep["groupe_compte"] == grp)
    ].copy()

    df_f["Facture"] = df_f.apply(facture_cell, axis=1)

    st.markdown(
        df_f[
            ["compte", "poste", "fournisseur", "montant_ttc", "Facture"]
        ].to_html(escape=False, index=False),
        unsafe_allow_html=True
    )

    st.download_button(
        "Télécharger base_depenses_immeuble.csv",
        df_f.to_csv(index=False).encode("utf-8"),
        file_name="base_depenses_immeuble.csv"
    )

    st.info(
        "Les restaurations et modifications sont temporaires.\n"
        "➡️ Télécharge les CSV et commit-les dans GitHub pour les rendre officielles."
    )