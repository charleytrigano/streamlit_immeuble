import streamlit as st
import pandas as pd
from pathlib import Path

# Configuration de base
st.set_page_config(page_title="Gestion des charges", layout="wide")
st.title("Gestion des charges")

# Chemins des fichiers
DATA_DIR = Path("data")
DEP_FILE = DATA_DIR / "depenses.csv"
BUD_FILE = DATA_DIR / "budget.csv"

# Créer le dossier et les fichiers s'ils n'existent pas
DATA_DIR.mkdir(exist_ok=True)

if not DEP_FILE.exists():
    pd.DataFrame(columns=["annee", "compte", "montant"]).to_csv(DEP_FILE, index=False)

if not BUD_FILE.exists():
    pd.DataFrame(columns=["annee", "compte", "budget"]).to_csv(BUD_FILE, index=False)

# Charger les données
@st.cache_data
def load_data():
    df_dep = pd.read_csv(DEP_FILE)
    df_bud = pd.read_csv(BUD_FILE)
    return df_dep, df_bud

# Sauvegarder les données
def save_data(df_dep, df_bud):
    df_dep.to_csv(DEP_FILE, index=False)
    df_bud.to_csv(BUD_FILE, index=False)
    st.success("Données sauvegardées !")

# Charger les données
df_dep, df_bud = load_data()

# Interface
st.sidebar.title("Actions")
if st.sidebar.button("Sauvegarder"):
    save_data(df_dep, df_bud)

page = st.sidebar.radio("Navigation", ["Dépenses", "Budget"])

if page == "Dépenses":
    st.header("Gestion des dépenses")

    # Afficher et éditer les dépenses
    edited_df = st.data_editor(df_dep, num_rows="dynamic")

    # Appliquer les modifications
    if not edited_df.equals(df_dep):
        df_dep = edited_df

    # Ajouter une dépense
    with st.form("Ajouter une dépense"):
        annee = st.number_input("Année", value=2025)
        compte = st.text_input("Compte")
        montant = st.number_input("Montant", value=0.0)

        if st.form_submit_button("Ajouter"):
            new_row = pd.DataFrame([{"annee": annee, "compte": compte, "montant": montant}])
            df_dep = pd.concat([df_dep, new_row], ignore_index=True)
            st.warning("Dépense ajoutée. Sauvegardez pour enregistrer.")

if page == "Budget":
    st.header("Gestion du budget")

    # Afficher et éditer le budget
    edited_bud = st.data_editor(df_bud, num_rows="dynamic")

    # Appliquer les modifications
    if not edited_bud.equals(df_bud):
        df_bud = edited_bud

    # Ajouter une ligne de budget
    with st.form("Ajouter une ligne de budget"):
        annee_bud = st.number_input("Année", value=2025)
        compte_bud = st.text_input("Compte")
        budget = st.number_input("Budget", value=0.0)

        if st.form_submit_button("Ajouter"):
            new_row_bud = pd.DataFrame([{"annee": annee_bud, "compte": compte_bud, "budget": budget}])
            df_bud = pd.concat([df_bud, new_row_bud], ignore_index=True
