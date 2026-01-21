import streamlit as st
import pandas as pd
from pathlib import Path
import os

# Configuration de base
st.set_page_config(page_title="Gestion des Charges", layout="wide")
st.title("🏠 Gestion des Charges de l'Immeuble")

# Chemins des fichiers
DATA_DIR = Path("data")
DEP_FILE = DATA_DIR / "depenses.csv"
BUD_FILE = DATA_DIR / "budget.csv"

# Créer le dossier et les fichiers s'ils n'existent pas
DATA_DIR.mkdir(exist_ok=True)

# Initialiser les fichiers CSV avec des colonnes de base
def init_files():
    if not DEP_FILE.exists():
        pd.DataFrame(columns=["annee", "compte", "poste", "montant"]).to_csv(DEP_FILE, index=False)
    if not BUD_FILE.exists():
        pd.DataFrame(columns=["annee", "compte", "budget"]).to_csv(BUD_FILE, index=False)

init_files()

# Charger les données avec gestion d'erreur
@st.cache_data
def load_data():
    try:
        df_dep = pd.read_csv(DEP_FILE)
        if df_dep.empty:
            df_dep = pd.DataFrame(columns=["annee", "compte", "poste", "montant"])
    except Exception as e:
        st.error(f"Erreur chargement dépenses: {e}")
        df_dep = pd.DataFrame(columns=["annee", "compte", "poste", "montant"])

    try:
        df_bud = pd.read_csv(BUD_FILE)
        if df_bud.empty:
            df_bud = pd.DataFrame(columns=["annee", "compte", "budget"])
    except Exception as e:
        st.error(f"Erreur chargement budget: {e}")
        df_bud = pd.DataFrame(columns=["annee", "compte", "budget"])

    return df_dep, df_bud

# Sauvegarder les données avec gestion d'erreur
def save_data(df_dep, df_bud):
    try:
        df_dep.to_csv(DEP_FILE, index=False)
        df_bud.to_csv(BUD_FILE, index=False)
        st.success("✅ Données sauvegardées avec succès !")
    except Exception as e:
        st.error(f"❌ Erreur sauvegarde: {e}")

# Charger les données
df_dep, df_bud = load_data()

# Sidebar
with st.sidebar:
    st.markdown("### 📁 Actions")
    if st.button("🔄 Recharger"):
        st.cache_data.clear()
        st.rerun()

    if st.button("💾 Sauvegarder"):
        save_data(df_dep, df_bud)

    st.markdown("### 📊 Navigation")
    page = st.radio("", ["Dépenses", "Budget"])

# Page Dépenses
if page == "Dépenses":
    st.header("📋 Gestion des Dépenses")

    # Filtres
    annees = [2025] if df_dep.empty else sorted(df_dep["annee"].unique())
    annee = st.selectbox("Année", annees)

    df_filtered = df_dep[df_dep["annee"] == annee] if not df_dep.empty else df_dep

    # Éditeur de données
    st.subheader("Liste des dépenses")
    edited_df = st.data_editor(
        df_filtered,
        num_rows="dynamic",
        key="depenses_editor"
    )

    # Appliquer les modifications
    if not edited_df.equals(df_filtered):
        df_dep.update(edited_df)
        st.warning("⚠️ Modifications appliquées. Sauvegardez pour enregistrer.")

    # Ajouter une dépense
    st.subheader("➕ Ajouter une dépense")
    with st.form("add_depense"):
        new_annee = st.number_input("Année", value=2025)
        new_compte = st.text_input("Compte")
        new_poste = st.text_input("Poste")
        new_montant = st.number_input("Montant", value=0.0)

        if st.form_submit_button("Ajouter"):
            new_row = pd.DataFrame([{
                "annee": new_annee,
                "compte": new_compte,
                "poste": new_poste,
                "montant": new_montant
            }])
            df_dep = pd.concat([df_dep, new_row], ignore_index=True)
            st.warning("⚠️ Dépense ajoutée. Sauvegardez pour enregistrer.")

    # Supprimer des dépenses
    st.subheader("❌ Supprimer des dépenses")
    if not df_filtered.empty:
        rows_to_delete = st.multiselect(
            "Lignes à supprimer",
            options=df_filtered.index,
            format_func=lambda x: f"Ligne {x}"
        )
        if st.button("Supprimer"):
            df_dep = df_dep.drop(rows_to_delete)
            st.warning("⚠️ Dépenses supprimées. Sauvegardez pour enregistrer.")

# Page Budget
if page == "Budget":
    st.header("💰 Gestion du Budget")

    # Filtres
    annees_bud = [2025] if df_bud.empty else sorted(df_bud["annee"].unique())
    annee_bud = st.selectbox("Année", annees_bud)

    df_bud_filtered = df_bud[df_bud["annee"] == annee_bud] if not df_bud.empty else df_bud

    # Éditeur de données
    st.subheader("Budget")
    edited_bud = st.data_editor(
        df_bud_filtered,
        num_rows="dynamic",
        key="budget_editor"
    )

    # Appliquer les modifications
    if not edited_bud.equals(df_bud_filtered):
        df_bud.update(edited_bud)
        st.warning("⚠️ Modifications appliquées. Sauvegardez pour enregistrer.")

    # Ajouter une ligne de budget
    st.subheader("➕ Ajouter une ligne de budget")
    with st.form("add_budget"):
        new_annee_bud = st.number_input("Année", value=2025)
        new_compte_bud = st.text_input("Compte")
        new_budget = st.number_input("Budget", value=0.0)

        if st.form_submit_button("Ajouter"):
            new_row_bud = pd.DataFrame([{
                "annee": new_annee_bud,
                "compte": new_compte_bud,
                "budget": new_budget
            }])
            df_bud = pd.concat([df_bud, new_row_bud], ignore_index=True)
            st.warning("⚠️ Ligne de budget ajoutée. Sauvegardez pour enregistrer.")

    # Supprimer des lignes de budget
    st.subheader("❌ Supprimer des lignes de budget")
    if not df_bud_filtered.empty:
        rows_to_delete_bud = st.multiselect(
            "Lignes à supprimer",
            options=df_bud_filtered.index,
            format_func=lambda x: f"Ligne {x}"
        )
        if st.button("Supprimer"):
            df_bud = df_bud.drop(rows_to_delete_bud)
            st.warning("⚠️ Lignes de budget supprimées. Sauvegardez pour enregistrer.")
