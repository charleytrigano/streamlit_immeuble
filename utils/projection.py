import pandas as pd

def project_baseline(df_pluri, annee_ref, horizon=2):
    """
    Projection mécanique basée sur la dernière variation connue
    """
    latest = df_pluri[df_pluri["Année"] == annee_ref]

    projections = []

    for _, row in latest.iterrows():
        montant = row["Montant_Total"]
        variation_pct = row.get("Variation %", 0) or 0

        for i in range(1, horizon + 1):
            annee_proj = annee_ref + i
            montant = montant * (1 + variation_pct / 100)

            projections.append({
                "Année": annee_proj,
                "Poste": row["Poste"],
                "Montant_Projeté": montant,
                "Scénario": "Tendance naturelle"
            })

    return pd.DataFrame(projections)


def apply_scenario(df_proj, reductions):
    """
    reductions : dict {poste: taux_reduction_en_%}
    """
    df = df_proj.copy()

    def ajust(row):
        taux = reductions.get(row["Poste"], 0)
        return row["Montant_Projeté"] * (1 - taux / 100)

    df["Montant_Projeté"] = df.apply(ajust, axis=1)
    df["Scénario"] = "Scénario économies"

    return df
