import streamlit as st
import pandas as pd
from pathlib import Path
import unicodedata
import os

# ======================================================
# CONFIG
# ======================================================
st.set_page_config(page_title="Pilotage des charges", layout="wide")
st.title("Pilotage des charges de l’immeuble")

DATA_DIR = Path("data")
DEP_FILE = DATA_DIR / "base_depenses_immeuble.csv"
BUD_FILE = DATA_DIR / "budget_comptes_generaux.csv"

# Créer le dossier data s'il n'existe pas
DATA_DIR.mkdir(exist_ok=True)

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
# CHARGEMENT ET SAUVEGARDE DES DONNÉES
# ======================================================
@st.cache_data(show_spinner=False)
def load_data():
    try:
        df_dep = pd.read_csv(DEP_FILE, sep=None, engine="python", encoding="utf-8-sig", on_bad_lines="skip")
        df_dep = normalize_depenses(df_dep)
    except FileNotFoundError:
        df_dep = pd.DataFrame(columns=["annee", "compte", "poste", "fournisseur", "montant_ttc", "piece_id", "pdf_url", "groupe_compte", "statut_facture"])

    try:
        df_bud = pd.read_csv(BUD_FILE, sep=None, engine="python", encoding="utf-8-sig", on_bad_lines="skip")
        df_bud = normalize_budget(df_bud)
    except FileNotFoundError:
        df_bud = pd.DataFrame(columns=["annee", "compte", "budget", "groupe_compte"])

    return df_dep, df_bud

def save_data(df_dep, df_bud):
    df_dep.to_csv(DEP_FILE, index=False)
    df_bud.to_csv(BUD_FILE, index=False)
    st.success("Données sauvegardées avec succès !")

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
# SIDEBAR
# ======================================================
with st.sidebar:
    st.markdown("## 📂 Données")

    if st.button("🔄 Recharger les données"):
        st.cache_data.clear()
        st.rerun()

    if st.button("💾 Sauvegarder les données"):
        save_data(df_dep, df_bud)

    page = st.radio(
        "Navigation",
        ["📊 État des dépenses", "💰 Budget", "📊 Budget vs Réel"]
    )

# ======================================================
# CHARGEMENT INITIAL
# ======================================================
df_dep, df_bud = load_data()

# ======================================================
# 📊 ÉTAT DES DÉPENSES (CRUD)
# ======================================================
if page == "📊 État des dépenses":
    st.markdown("### 🔎 Filtres")
    f1, f2, f3, f4 = st.columns(4)
    with f1:
        annee = st.selectbox("Année", sorted(df_dep["annee"].unique()) if not df_dep.empty else [2025])
    with f2:
        groupe = st.selectbox(
            "Groupe de comptes",
            ["Tous"] + sorted(df_dep["groupe_compte"].unique()) if not df_dep.empty else ["Tous"]
        )
    with f3:
        fournisseur = st.selectbox(
            "Fournisseur",
            ["Tous"] + sorted(df_dep["fournisseur"].unique()) if not df_dep.empty else ["Tous"]
        )
    with f4:
        statut = st.selectbox(
            "Statut facture",
            ["Tous", "Justifiée", "À justifier"]
        )

    df_f = df_dep[df_dep["annee"] == annee].copy() if not df_dep.empty else df_dep.copy()
    if groupe != "Tous" and not df_f.empty:
        df_f = df_f[df_f["groupe_compte"] == groupe]
    if fournisseur != "Tous" and not df_f.empty:
        df_f = df_f[df_f["fournisseur"] == fournisseur]
    if statut != "Tous" and not df_f.empty:
        df_f = df_f[df_f["statut_facture"] == statut]

    # KPI
    dep_pos = df_f[df_f["montant_ttc"] > 0]["montant_ttc"].sum() if not df_f.empty else 0
    dep_neg = df_f[df_f["montant_ttc"] < 0]["montant_ttc"].sum() if not df_f.empty else 0
    net = dep_pos + dep_neg
    pct_ok = (df_f["statut_facture"] == "Justifiée").mean() * 100 if not df_f.empty else 0

    k1, k2, k3, k4 = st.columns(4)
    k1.metric("Dépenses brutes (€)", f"{dep_pos:,.0f}".replace(",", " "))
    k2.metric("Avoirs (€)", f"{dep_neg:,.0f}".replace(",", " "))
    k3.metric("Dépenses nettes (€)", f"{net:,.0f}".replace(",", " "))
    k4.metric("% justifiées", f"{pct_ok:.0f} %")

    # Édition
    st.markdown("### ✏️ Modifier les dépenses")
    edited_df = st.data_editor(
        df_f,
        num_rows="dynamic",
        use_container_width=True,
        key="edit_dep"
    )

    # Appliquer les modifications au DataFrame principal
    if not edited_df.equals(df_f):
        df_dep.update(edited_df)
        st.warning("Modifications appliquées. Pensez à sauvegarder !")

    # Ajouter une nouvelle dépense
    st.markdown("### ➕ Ajouter une dépense")
    with st.form("new_depense"):
        new_annee = st.number_input("Année", value=2025)
        new_compte = st.text_input("Compte")
        new_poste = st.text_input("Poste")
        new_fournisseur = st.text_input("Fournisseur")
        new_montant = st.number_input("Montant TTC", value=0.0)
        new_piece_id = st.text_input("ID Pièce")
        new_pdf_url = st.text_input("URL PDF")
        submitted = st.form_submit_button("Ajouter")
        if submitted:
            new_row = pd.DataFrame([{
                "annee": new_annee,
                "compte": new_compte,
                "poste": new_poste,
                "fournisseur": new_fournisseur,
                "montant_ttc": new_montant,
                "piece_id": new_piece_id,
                "pdf_url": new_pdf_url,
                "groupe_compte": compute_groupe_compte(new_compte),
                "statut_facture": "Justifiée" if new_pdf_url else "À justifier"
            }])
            df_dep = pd.concat([df_dep, new_row], ignore_index=True)
            st.warning("Dépense ajoutée. Pensez à sauvegarder !")

    # Supprimer une dépense
    st.markdown("### ❌ Supprimer une dépense")
    if not df_f.empty:
        rows_to_delete = st.multiselect(
            "Sélectionner les lignes à supprimer",
            options=df_f.index,
            format_func=lambda x: f"Ligne {x}"
        )
        if st.button("Supprimer"):
            df_dep = df_dep.drop(rows_to_delete)
            st.warning("Dépenses supprimées. Pensez à sauvegarder !")

    # Affichage
    if not df_f.empty:
        df_f["Facture"] = df_f.apply(make_facture_cell, axis=1)
        df_f["Montant (€)"] = df_f["montant_ttc"].map(
            lambda x: f"{x:,.2f}".replace(",", " ")
        )
        st.markdown(
            df_f[
                ["compte", "poste", "fournisseur", "Montant (€)", "statut_facture", "Facture"]
            ].to_html(escape=False, index=False),
            unsafe_allow_html=True
        )

    st.download_button(
        "💾 Télécharger base_depenses_immeuble.csv",
        df_dep.to_csv(index=False).encode("utf-8"),
        file_name="base_depenses_immeuble.csv",
        mime="text/csv",
    )

# ======================================================
# 💰 BUDGET (CRUD)
# ======================================================
if page == "💰 Budget":
    annee = st.selectbox("Année budgétaire", sorted(df_bud["annee"].unique()) if not df_bud.empty else [2025])
    df_b = df_bud[df_bud["annee"] == annee].copy() if not df_bud.empty else df_bud.copy()

    st.metric("Budget total (€)", f"{df_b['budget'].sum():,.0f}".replace(",", " ") if not df_b.empty else "0")

    # Édition
    st.markdown("### ✏️ Modifier le budget")
    edited_bud = st.data_editor(
        df_b,
        num_rows="dynamic",
        use_container_width=True,
        key="edit_budget"
    )

    # Appliquer les modifications au DataFrame principal
    if not edited_bud.equals(df_b):
        df_bud.update(edited_bud)
        st.warning("Modifications appliquées. Pensez à sauvegarder !")

    # Ajouter une nouvelle ligne de budget
    st.markdown("### ➕ Ajouter une ligne de budget")
    with st.form("new_budget"):
        new_annee_bud = st.number_input("Année", value=2025)
        new_compte_bud = st.text_input("Compte")
        new_budget = st.number_input("Budget", value=0.0)
        submitted_bud = st.form_submit_button("Ajouter")
        if submitted_bud:
            new_row_bud = pd.DataFrame([{
                "annee": new_annee_bud,
                "compte": new_compte_bud,
                "budget": new_budget,
                "groupe_compte": compute_groupe_compte(new_compte_bud)
            }])
            df_bud = pd.concat([df_bud, new_row_bud], ignore_index=True)
            st.warning("Ligne de budget ajoutée. Pensez à sauvegarder !")

    # Supprimer une ligne de budget
    st.markdown("### ❌ Supprimer une ligne de budget")
    if not df_b.empty:
        rows_to_delete_bud = st.multiselect(
            "Sélectionner les lignes à supprimer",
            options=df_b.index,
            format_func=lambda x: f"Ligne {x}"
        )
        if st.button("Supprimer"):
            df_bud = df_bud.drop(rows_to_delete_bud)
            st.warning("Lignes de budget supprimées. Pensez à sauvegarder !")

    st.download_button(
        "💾 Télécharger budget_comptes_generaux.csv",
        df_bud.to_csv(index=False).encode("utf-8"),
        file_name="budget_comptes_generaux.csv",
        mime="text/csv",
    )

# ======================================================
# 📊 BUDGET VS RÉEL
# ======================================================
if page == "📊 Budget vs Réel":
    annee = st.selectbox("Année", sorted(df_dep["annee"].unique()) if not df_dep.empty else [2025])

    dep = df_dep[df_dep["annee"] == annee] if not df_dep.empty else df_dep
    bud = df_bud[df_bud["annee"] == annee] if not df_bud.empty else df_bud

    reel = dep.groupby("groupe_compte")["montant_ttc"].sum().reset_index() if not dep.empty else pd.DataFrame(columns=["groupe_compte", "montant_ttc"])
    comp = bud.merge(reel, on="groupe_compte", how="left").fillna(0) if not bud.empty else pd.DataFrame(columns=["groupe_compte", "budget", "montant_ttc"])

    comp["Écart (€)"] = comp["montant_ttc"] - comp["budget"]
    comp["Écart (%)"] = (comp["Écart (€)"] / comp["budget"] * 100).round(1)

    k1, k2, k3 = st.columns(3)
    k1.metric("Budget (€)", f"{comp['budget'].sum():,.0f}".replace(",", " ") if not comp.empty else "0")
    k2.metric("Réel (€)", f"{comp['montant_ttc'].sum():,.0f}".replace(",", " ") if not comp.empty else "0")
    k3.metric("Écart total (€)", f"{comp['Écart (€)'].sum():,.0f}".replace(",", " ") if not comp.empty else "0")

    st.dataframe(
        comp[
            ["groupe_compte", "budget", "montant_ttc", "Écart (€)", "Écart (%)"]
        ],
        use_container_width=True
    )
