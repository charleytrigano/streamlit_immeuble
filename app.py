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


def make_facture_cell(row):
    pid = row.get("piece_id", "")
    url = row.get("pdf_url", "")
    if isinstance(url, str) and url.strip():
        return f'{pid} – <a href="{url}" target="_blank">📄 Ouvrir</a>'
    return pid if pid else "—"


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
        st.error(f"Colonnes manquantes dans les dépenses : {required - set(df.columns)}")
        st.stop()

    df["annee"] = df["annee"].astype(int)
    df["compte"] = df["compte"].astype(str)
    df["montant_ttc"] = df["montant_ttc"].astype(float)
    df["piece_id"] = df["piece_id"].astype(str).str.strip()
    df["pdf_url"] = df["pdf_url"].astype(str).str.strip()
    df["groupe_compte"] = df["compte"].apply(compute_groupe_compte)

    df["statut_facture"] = df["pdf_url"].apply(
        lambda x: "Justifiée" if x else "À justifier"
    )

    return df


def normalize_budget(df):
    df = clean_columns(df)

    required = {"annee", "compte", "budget"}
    if not required.issubset(df.columns):
        st.error(f"Colonnes manquantes dans le budget : {required - set(df.columns)}")
        st.stop()

    df["annee"] = df["annee"].astype(int)
    df["compte"] = df["compte"].astype(str)
    df["budget"] = df["budget"].astype(float)
    df["groupe_compte"] = df["compte"].apply(compute_groupe_compte)

    return df


# ======================================================
# CHARGEMENT DES DONNÉES
# ======================================================
@st.cache_data(show_spinner=False)
def load_data():
    df_dep = normalize_depenses(
        pd.read_csv(
            DEP_FILE,
            sep=None,
            engine="python",
            encoding="utf-8-sig",
            on_bad_lines="skip",
        )
    )

    df_bud = normalize_budget(
        pd.read_csv(
            BUD_FILE,
            sep=None,
            engine="python",
            encoding="utf-8-sig",
            on_bad_lines="skip",
        )
    )

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

    page = st.radio(
        "Navigation",
        ["📊 État des dépenses", "💰 Budget", "📊 Budget vs Réel"]
    )

# ======================================================
# 📊 ÉTAT DES DÉPENSES
# ======================================================
if page == "📊 État des dépenses":

    st.markdown("### 🔎 Filtres")

    f1, f2, f3, f4 = st.columns(4)
    with f1:
        annee = st.selectbox("Année", sorted(df_dep["annee"].unique()))
    with f2:
        groupe = st.selectbox(
            "Groupe de comptes",
            ["Tous"] + sorted(df_dep["groupe_compte"].unique())
        )
    with f3:
        fournisseur = st.selectbox(
            "Fournisseur",
            ["Tous"] + sorted(df_dep["fournisseur"].unique())
        )
    with f4:
        statut = st.selectbox(
            "Statut facture",
            ["Tous", "Justifiée", "À justifier"]
        )

    df_f = df_dep[df_dep["annee"] == annee].copy()
    if groupe != "Tous":
        df_f = df_f[df_f["groupe_compte"] == groupe]
    if fournisseur != "Tous":
        df_f = df_f[df_f["fournisseur"] == fournisseur]
    if statut != "Tous":
        df_f = df_f[df_f["statut_facture"] == statut]

    # KPI
    dep_pos = df_f[df_f["montant_ttc"] > 0]["montant_ttc"].sum()
    dep_neg = df_f[df_f["montant_ttc"] < 0]["montant_ttc"].sum()
    net = dep_pos + dep_neg
    pct_ok = (df_f["statut_facture"] == "Justifiée").mean() * 100 if len(df_f) else 0

    k1, k2, k3, k4 = st.columns(4)
    k1.metric("Dépenses brutes (€)", f"{dep_pos:,.0f}".replace(",", " "))
    k2.metric("Avoirs (€)", f"{dep_neg:,.0f}".replace(",", " "))
    k3.metric("Dépenses nettes (€)", f"{net:,.0f}".replace(",", " "))
    k4.metric("% justifiées", f"{pct_ok:.0f} %")

    # Édition
    st.markdown("### ✏️ Modifier les dépenses")
    df_edit = st.data_editor(
        df_f,
        num_rows="dynamic",
        use_container_width=True,
        key="edit_dep"
    )

    df_edit["Facture"] = df_edit.apply(make_facture_cell, axis=1)
    df_edit["Montant (€)"] = df_edit["montant_ttc"].map(
        lambda x: f"{x:,.2f}".replace(",", " ")
    )

    st.markdown(
        df_edit[
            ["compte", "poste", "fournisseur", "Montant (€)", "statut_facture", "Facture"]
        ].to_html(escape=False, index=False),
        unsafe_allow_html=True
    )

    st.download_button(
        "💾 Télécharger base_depenses_immeuble.csv",
        df_edit.to_csv(index=False).encode("utf-8"),
        file_name="base_depenses_immeuble.csv",
        mime="text/csv",
    )

    st.info(
        "Les modifications sont locales à la session.\n"
        "➡️ Télécharge le CSV et commit-le dans GitHub pour les conserver."
    )

# ======================================================
# 💰 BUDGET
# ======================================================
if page == "💰 Budget":

    annee = st.selectbox("Année budgétaire", sorted(df_bud["annee"].unique()))
    df_b = df_bud[df_bud["annee"] == annee].copy()

    st.metric("Budget total (€)", f"{df_b['budget'].sum():,.0f}".replace(",", " "))

    st.markdown("### ✏️ Modifier le budget")
    df_edit = st.data_editor(
        df_b,
        num_rows="dynamic",
        use_container_width=True,
        key="edit_budget"
    )

    st.download_button(
        "💾 Télécharger budget_comptes_generaux.csv",
        df_edit.to_csv(index=False).encode("utf-8"),
        file_name="budget_comptes_generaux.csv",
        mime="text/csv",
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

    k1, k2, k3 = st.columns(3)
    k1.metric("Budget (€)", f"{comp['budget'].sum():,.0f}".replace(",", " "))
    k2.metric("Réel (€)", f"{comp['montant_ttc'].sum():,.0f}".replace(",", " "))
    k3.metric("Écart total (€)", f"{comp['Écart (€)'].sum():,.0f}".replace(",", " "))

    st.dataframe(
        comp[
            ["groupe_compte", "budget", "montant_ttc", "Écart (€)", "Écart (%)"]
        ],
        use_container_width=True
    )
