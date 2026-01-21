import streamlit as st
import pandas as pd
from pathlib import Path
import os

# Configuration de base
st.set_page_config(page_title="Pilotage des charges", layout="wide")
st.title("Pilotage des charges de l’immeuble")

# Chemins des fichiers
DATA_DIR = Path("data")
DEP_FILE = DATA_DIR / "base_depenses_immeuble.csv"
BUD_FILE = DATA_DIR / "budget_comptes_generaux.csv"

# Créer le dossier data s'il n'existe pas
DATA_DIR.mkdir(exist_ok=True)

# Initialiser les DataFrames si les fichiers n'existent pas
if not DEP_FILE.exists():
    pd.DataFrame(columns=["annee", "compte", "poste", "fournisseur", "montant_ttc", "piece_id", "pdf_url"]).to_csv(DEP_FILE, index=False)

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
    st.success("Données sauvegardées avec succès !")

# Charger les données
df_dep, df_bud = load_data()

# Sidebar
with st.sidebar:
    st.markdown("## 📂 Données")
    if st.button("🔄 Recharger"):
        st.cache_data.clear()
        st.rerun()

    if st.button("💾 Sauvegarder"):
        save_data(df_dep, df_bud)

    page = st.radio("Navigation", ["📊 Dépenses", "💰 Budget", "📊 Budget vs Réel"])

# Page Dépenses
if page == "📊 Dépenses":
    st.header("Gestion des dépenses")

    # Filtres
    annees = sorted(df_dep["annee"].unique()) if not df_dep.empty else [2025]
    annee = st.selectbox("Année", annees)

    df_filtered = df_dep[df_dep["annee"] == annee] if not df_dep.empty else df_dep.copy()

    # Affichage des dépenses
    st.subheader("Liste des dépenses")
    edited_df = st.data_editor(
        df_filtered,
        num_rows="dynamic",
        key="edit_depenses"
    )

    # Appliquer les modifications
    if not edited_df.equals(df_filtered):
        df_dep.update(edited_df)
        st.warning("Modifications appliquées. Pensez à sauvegarder.")

    # Ajouter une dépense
    st.subheader("Ajouter une dépense")
    with st.form("add_depense"):
        new_annee = st.number_input("Année", value=2025)
        new_compte = st.text_input("Compte")
        new_poste = st.text_input("Poste")
        new_fournisseur = st.text_input("Fournisseur")
        new_montant = st.number_input("Montant TTC", value=0.0)
        new_piece_id = st.text_input("ID Pièce")
        new_pdf_url = st.text_input("URL PDF")

        if st.form_submit_button("Ajouter"):
            new_row = pd.DataFrame([{
                "annee": new_annee,
                "compte": new_compte,
                "poste": new_poste,
                "fournisseur": new_fournisseur,
                "montant_ttc": new_montant,
                "piece_id": new_piece_id,
                "pdf_url": new_pdf_url
            }])
            df_dep = pd.concat([df_dep, new_row], ignore_index=True)
            st.warning("Dépense ajoutée. Pensez à sauvegarder.")

    # Supprimer des dépenses
    st.subheader("Supprimer des dépenses")
    if not df_filtered.empty:
        rows_to_delete = st.multiselect(
            "Lignes à supprimer",
            options=df_filtered.index,
            format_func=lambda x: f"Ligne {x}"
        )
        if st.button("Supprimer"):
            df_dep = df_dep.drop(rows_to_delete)
            st.warning("Dépenses supprimées. Pensez à sauvegarder.")

# Page Budget
if page == "💰 Budget":
    st.header("Gestion du budget")

    # Filtres
    annees_bud = sorted(df_bud["annee"].unique()) if not df_bud.empty else [2025]
    annee_bud = st.selectbox("Année", annees_bud)

    df_bud_filtered = df_bud[df_bud["annee"] == annee_bud] if not df_bud.empty else df_bud.copy()

    # Affichage du budget
    st.subheader("Budget")
    edited_bud = st.data_editor(
        df_bud_filtered,
        num_rows="dynamic",
        key="edit_budget"
    )

    # Appliquer les modifications
    if not edited_bud.equals(df_bud_filtered):
        df_bud.update(edited_bud)
        st.warning("Modifications appliquées. Pensez à sauvegarder.")

    # Ajouter une ligne de budget
    st.subheader("Ajouter une ligne de budget")
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
            st.warning("Ligne de budget ajoutée. Pensez à sauvegarder.")

    # Supprimer des lignes de budget
    st.subheader("Supprimer des lignes de budget")
    if not df_bud_filtered.empty:
        rows_to_delete_bud = st.multiselect(
            "Lignes à supprimer",
            options=df_bud_filtered.index,
            format_func=lambda x: f"Ligne {x}"
        )
        if st.button("Supprimer"):
            df_bud = df_bud.drop(rows_to_delete_bud)
            st.warning("Lignes de budget supprimées. Pensez à sauvegarder.")

# Page Budget vs Réel
if page == "📊 Budget vs Réel":
    st.header("Comparaison Budget vs Réel")

    annee_comp = st.selectbox("Année", sorted(df_dep["annee"].unique()) if not df_dep.empty else [2025])

    df_dep_comp = df_dep[df_dep["annee"] == annee_comp] if not df_dep.empty else df_dep
    df_bud_comp = df_bud[df_bud["annee"] == annee_comp] if not df_bud.empty else df_bud

    # Calcul des écarts
    reel = df_dep_comp.groupby("compte")["montant_ttc"].sum().reset_index()
    comp = df_bud_comp.merge(reel, on="compte", how="left").fillna(0)
    comp["Écart (€)"] = comp["montant_ttc"] - comp["budget"]
    comp["Écart (%)"] = (comp["Écart (€)"] / comp["budget"] * 100).round(1)

    st.dataframe(comp[["compte", "budget", "montant_ttc", "Écart (€)", "Écart (%)"]])
