import pandas as pd

def aggregate_pluriannuel(dfs):
    """
    dfs : liste de DataFrames factures (toutes années)
    """
    df_all = pd.concat(dfs, ignore_index=True)

    synthese = (
        df_all.groupby(["Année", "Poste"])
        .agg(
            Montant_Total=("Montant TTC", "sum"),
            Nb_Factures=("Fichier", "count"),
            Nb_Fournisseurs=("Fournisseur", "nunique")
        )
        .reset_index()
    )

    return synthese


def compute_trends(df_pluri):
    """
    Calcule évolution N vs N-1 par poste
    """
    df = df_pluri.sort_values(["Poste", "Année"])

    df["Variation €"] = (
        df.groupby("Poste")["Montant_Total"]
        .diff()
    )

    df["Variation %"] = (
        df.groupby("Poste")["Montant_Total"]
        .pct_change() * 100
    )

    return df
