import streamlit as st
import pandas as pd
from utils.analyse import analyse_pdfs

st.set_page_config(page_title="Analyse charges immeuble", layout="wide")

st.title("Analyse facture par facture – Immeuble")

annee = st.number_input("Année analysée", value=2025, step=1)

st.markdown("### Upload des factures par compte")

structure = {}

comptes = st.text_area(
    "Liste des comptes (1 par ligne, noms exacts des dossiers)",
    "Entretien plomberie\nContrat entretien ascenseur\nEau"
).splitlines()

for compte in comptes:
    if compte.strip():
        files = st.file_uploader(
            f"Factures PDF – {compte}",
            type="pdf",
            accept_multiple_files=True
        )
        if files:
            structure[compte] = files

if st.button("Lancer l'analyse"):
    if not structure:
        st.warning("Veuillez uploader au moins un dossier de factures.")
    else:
        df = analyse_pdfs(structure, annee)

        st.success("Analyse terminée")
        st.dataframe(df, use_container_width=True)

        synthese = (
            df.groupby(["Compte", "Poste"])
              .agg(
                  Montant_Total=("Montant TTC", "sum"),
                  Nb_Factures=("Fichier", "count"),
                  Nb_Fournisseurs=("Fournisseur", "nunique")
              )
              .reset_index()
        )

        st.markdown("### Synthèse par poste")
        st.dataframe(synthese, use_container_width=True)

        output = "analyse_factures.xlsx"
        with pd.ExcelWriter(output, engine="openpyxl") as writer:
            df.to_excel(writer, sheet_name="Factures", index=False)
            synthese.to_excel(writer, sheet_name="Synthese", index=False)

        with open(output, "rb") as f:
            st.download_button(
                "Télécharger l'analyse Excel",
                f,
                file_name=output
            )

