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


def compute_groupe_compte(compte):
    compte = str(compte)
    return compte[:4] if compte.startswith(("621", "622")) else compte[:3]


def make_facture_link(row):
    if row["pdf_url"] in ("", "nan"):
        return row["piece_id"]
    return f'{row["piece_id"]} – <a href="{row["pdf_url"]}" target="_blank">📄 Ouvrir</a>'


def build_drive_search_url(folder_url, piece_id):
    if folder_url.strip() == "" or piece_id.strip() == "":
        return ""
    return f"{folder_url}?q={piece_id.replace(' ', '%20')}"

# ======================================================
# NORMALISATION
# ======================================================
def normalize_depenses(df):
    df = clean_columns(df)

    for col in ["poste", "fournisseur", "piece_id", "pdf_url"]:
        if col not in df.columns:
            df[col] = ""

    required = {"annee", "compte", "montant_ttc"}
    if not required.issubset(df.columns):
        st.error(f"Colonnes manquantes : {required - set(df.columns)}")
        st.stop()

    df["annee"] = df["annee"].astype(int)
    df["compte"] = df["compte"].astype(str)
    df["montant_ttc"] = df["montant_ttc"].astype(float)
    df["piece_id"] = df["piece_id"].astype(str).str.strip()
    df["pdf_url"] = df["pdf_url"].astype(str).str.strip()
    df["groupe_compte"] = df["compte"].apply(compute_groupe_compte)

    return df


def normalize_budget(df):
    df = clean_columns(df)

    required = {"annee", "compte", "budget"}
    if not required.issubset(df.columns):
        st.error(f"Colonnes manquantes : {required - set(df.columns)}")
        st.stop()

    df["annee"] = df["annee"].astype(int)
    df["compte"] = df["compte"].astype(str)
    df["budget"] = df["budget"].astype(float)
    df["groupe_compte"] = df["compte"].apply(compute_groupe_compte)

    return df

# ======================================================
# CHARGEMENT
# ======================================================
@st.cache_data
def load_data():
    df_dep = normalize_depenses(pd.read_csv(DEP_FILE, encoding="utf-8-sig"))
    ddf_bud = normalize_budget(
    pd.read_csv(
        BUD_FILE,
        sep=None,                 # auto-détection du séparateur
        engine="python",          # parseur tolérant
        encoding="utf-8-sig",
        on_bad_lines="skip"       # ignore les lignes corrompues
    )
)
f_bud = normalize_budget(pd.read_csv(BUD_FILE, encoding="utf-8-sig"))
    return df_dep, df_bud


df_dep, df_bud = load_data()

# ======================================================
# SIDEBAR
# ======================================================
with st.sidebar:
    st.markdown("## 📂 Données")
    if st.button("🔄 Recharger les données"):
        st.cache_data.clear()
        st.rerun()

    st.markdown("## 📁 Google Drive")
    drive_folder = st.text_input(
        "Lien du dossier Google Drive (année)",
        placeholder="https://drive.google.com/drive/folders/XXXX"
    )

    page = st.radio(
        "Navigation",
        ["📊 État des dépenses", "💰 Budget", "📊 Budget vs Réel"]
    )

# ======================================================
# 📊 ÉTAT DES DÉPENSES — ÉDITION + AUTO PDF
# ======================================================
if page == "📊 État des dépenses":

    annee = st.selectbox("Année", sorted(df_dep["annee"].unique()))
    df_f = df_dep[df_dep["annee"] == annee].copy()

    st.markdown("### ✏️ Modifier les dépenses")
    df_edit = st.data_editor(
        df_f,
        num_rows="dynamic",
        use_container_width=True,
        key="edit_dep"
    )

    if drive_folder:
        st.markdown("### 🔗 Génération automatique des liens PDF")
        df_edit["pdf_url"] = df_edit.apply(
            lambda r: r["pdf_url"]
            if r["pdf_url"] not in ("", "nan")
            else build_drive_search_url(drive_folder, r["piece_id"]),
            axis=1
        )

    df_edit["Facture"] = df_edit.apply(make_facture_link, axis=1)

    st.markdown("### 📋 Aperçu")
    st.markdown(
        df_edit[
            ["compte", "poste", "fournisseur", "montant_ttc", "Facture"]
        ].to_html(escape=False, index=False),
        unsafe_allow_html=True
    )

    st.download_button(
        "💾 Télécharger base_depenses_immeuble.csv",
        df_edit.to_csv(index=False).encode("utf-8"),
        file_name="base_depenses_immeuble.csv",
        mime="text/csv"
    )

    st.info("⚠️ Les modifications sont sauvegardées uniquement après commit GitHub.")

# ======================================================
# 💰 BUDGET — ÉDITION
# ======================================================
if page == "💰 Budget":

    annee = st.selectbox("Année budgétaire", sorted(df_bud["annee"].unique()))
    df_b = df_bud[df_bud["annee"] == annee]

    st.markdown("### ✏️ Modifier le budget")
    df_edit = st.data_editor(
        df_b,
        num_rows="dynamic",
        use_container_width=True,
        key="edit_budget"
    )

    st.metric("Budget total (€)", f"{df_edit['budget'].sum():,.0f}".replace(",", " "))

    st.download_button(
        "💾 Télécharger budget_comptes_generaux.csv",
        df_edit.to_csv(index=False).encode("utf-8"),
        file_name="budget_comptes_generaux.csv",
        mime="text/csv"
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

    st.dataframe(comp, use_container_width=True)
