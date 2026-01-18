import pandas as pd
from config import COMPTE_TO_POSTE
from utils.pdf_utils import extract_text, extract_amount, extract_date

def analyse_pdfs(structure, annee):
    rows = []

    for compte, files in structure.items():
        poste = COMPTE_TO_POSTE.get(compte, compte)

        for pdf in files:
            text = extract_text(pdf)
            rows.append({
                "Année": annee,
                "Compte": compte,
                "Poste": poste,
                "Fournisseur": pdf.name.replace(".pdf", ""),
                "Montant TTC": extract_amount(text),
                "Date": extract_date(text),
                "Fichier": pdf.name
            })

    df = pd.DataFrame(rows)

    df["Récurrent"] = (
        df.groupby(["Compte", "Fournisseur"])["Fichier"]
        .transform("count") > 1
    )

    df["Type"] = df["Récurrent"].apply(
        lambda x: "Contrat / récurrent" if x else "Intervention ponctuelle"
    )

    return df

