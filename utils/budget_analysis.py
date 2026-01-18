import pandas as pd

def analyse_budget_vs_reel(df_factures, df_budget):
    reel = (
        df_factures.groupby("Poste")["Montant TTC"]
        .sum()
        .reset_index()
        .rename(columns={"Montant TTC": "Réel"})
    )

    df = reel.merge(df_budget, on="Poste", how="left")

    df["Écart €"] = df["Réel"] - df["Budget"]
    df["Écart %"] = (df["Écart €"] / df["Budget"]) * 100

    def statut(row):
        if pd.isna(row["Budget"]):
            return "⚠️ Budget manquant"
        if row["Écart €"] > 0:
            return "❌ Dépassement"
        return "✅ Conforme"

    df["Statut"] = df.apply(statut, axis=1)

    return df.sort_values("Écart €", ascending=False)

