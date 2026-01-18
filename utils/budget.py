import pandas as pd

def load_budget(uploaded_file):
    df = pd.read_excel(uploaded_file)
    df.columns = [c.strip() for c in df.columns]

    if "Poste" not in df.columns or "Budget" not in df.columns:
        raise ValueError("Le fichier budget doit contenir les colonnes 'Poste' et 'Budget'")

    return df[["Poste", "Budget"]]

