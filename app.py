import streamlit as st
import pandas as pd

from utils.analyse import analyse_pdfs
from utils.graphs import (
    plot_charges_par_poste,
    plot_pareto_postes,
    plot_top_fournisseurs,
    plot_recurrent_vs_ponctuel
)

# -------------------------------------------------
# CONFIG STREAMLIT
# -------------------------------------------------
st.set_page_config(
    page_title="Analyse des charges de l'immeuble",
    layout="wide"
)

st.title("Analyse facture par facture – Gestion de l’immeuble")
st.markdown(
    """
    Cette application permet d’analyser **facture par facture** les charges de l’immeuble,
    afin d’identifier les **postes coûteux**, les **prestataires dominants** et les
    **leviers de réduction des frais**.
    """
)

# -------------------------------------------------
# PARAMÈTRES GÉNÉRAUX
# -------------------------------------------------
st.sidebar.header("Paramètres")

annee = st.sidebar.number_input(
    "Année analysée",
    value=2025,
    step=1
)

st.sidebar.markdown("---")
st.sidebar.markdown(
    """
    **Mode d’utilisation**
    1. Indiquez les comptes comptables  
    2. Uploadez les factures PDF par compte  
    3. Lancez l’analyse  
    """
)

# -------------------------------------------------
# SAISIE DES COMPTES
# -------------------------------------------------
st.markdown("## 1️⃣ Comptes comptables")

comptes = st.text_area(
    "Liste des comptes (1 par ligne — noms EXACTS des dossiers)",
    height=150,
    placeholder="Entretien plomberie\nContrat entretien ascenseur\nEau\nAssurances"
)

liste_comptes = [c.strip() for c in comptes.splitlines() if c.strip()]

# -------------------------------------------------
# UPLOAD DES FACTURES
# -------------------------------------------------
st.markdown("## 2️⃣ Upload des factures PDF")

structure = {}

if liste_comptes:
    for compte in liste_comptes:
        fichiers = st.file_uploader(
            f"📂 {compte}",
            type="pdf",
            accept_multiple_files=True,
            key=compte
        )
        if fichiers:
            structure[compte] = fichiers
else:
    st.info("Veuillez saisir au moins un compte comptable.")

# -------------------------------------------------
# LANCEMENT DE L’ANALYSE
# -------------------------------------------------
st.markdown("## 3️⃣ Lancer l’analyse")

if st.button("🚀 Analyser les factures"):
    if not structure:
        st.warning("Aucune facture PDF n’a été uploadée.")
    else:
        with st.spinner("Analyse des factures en cours..."):
            df = analyse_pdfs(structure, annee)

        st.success("Analyse terminée")

        # -------------------------------------------------
        # TABLE FACTURES
        # -------------------------------------------------
        st.markdown("## 📄 Détail des factures")
        st.dataframe(df, use_container_width=True)

        # -------------------------------------------------
        # SYNTHÈSE PAR POSTE
        # -------------------------------------------------
        st.markdown("## 📊 Synthèse par poste")

        synthese = (
            df.groupby(["Compte", "Poste"])
              .agg(
                  Montant_Total=("Montant TTC", "sum"),
                  Nb_Factures=("Fichier", "count"),
                  Nb_Fournisseurs=("Fournisseur", "nunique")
              )
              .reset_index()
              .sort_values("Montant_Total", ascending=False)
        )

        st.dataframe(synthese, use_container_width=True)

        # -------------------------------------------------
        # FILTRES GRAPHIQUES
        # -------------------------------------------------
        st.markdown("## 🔍 Filtres d’analyse")

        col1, col2 = st.columns(2)
