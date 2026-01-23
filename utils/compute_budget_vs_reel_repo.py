import pandas as pd

# Comptes exceptionnels à 4 chiffres
EXCEPTIONS_4_CHIFFRES = ("6211", "6213", "6222", "6223")


def compute_groupe_compte(compte: str) -> str:
    """
    Calcule le groupe de compte selon la règle métier :
    - 4 chiffres pour certaines exceptions
    - 3 chiffres dans tous les autres cas
    """
    compte = str(compte).strip()

    for exc in EXCEPTIONS_4_CHIFFRES:
        if compte.startswith(exc):
            return compte[:4]

    return compte[:3]


def compute_budget_vs_reel(df_budget: pd.DataFrame, df_depenses: pd.DataFrame) -> pd.DataFrame:
    """
    Calcule le comparatif Budget vs Réel par année et groupe de compte
    """

    # --- Sécurisation minimale ---
    df_budget = df_budget.copy()
    df_depenses = df_depenses.copy()

    # Normalisation types
    df_budget["annee"] = df_budget["annee"].astype(int)
    df_budget["compte"] = df_budget["compte"].astype(str)

    df_depenses["annee"] = df_depenses["annee"].astype(int)
    df_depenses["compte"] = df_depenses["compte"].astype(str)
    df_depenses["montant_ttc"] = df_depenses["montant_ttc"].astype(float)

    # --- Calcul du groupe de compte ---
    df_budget["groupe_compte"] = df_budget["compte"].apply(compute_groupe_compte)
    df_depenses["groupe_compte"] = df_depenses["compte"].apply(compute_groupe_compte)

    # --- Agrégation ---
    budget_agg = (
        df_budget
        .groupby(["annee", "groupe_compte"], as_index=False)
        .agg(budget=("budget", "sum"))
    )

    depenses_agg = (
        df_depenses
        .groupby(["annee", "groupe_compte"], as_index=False)
        .agg(depenses_reelles=("montant_ttc", "sum"))
    )

    # --- Fusion ---
    comp = pd.merge(
        budget_agg,
        depenses_agg,
        on=["annee", "groupe_compte"],
        how="left"
    )

    comp["depenses_reelles"] = comp["depenses_reelles"].fillna(0)

    # --- KPI ---
    comp["ecart_eur"] = comp["depenses_reelles"] - comp["budget"]
    comp["ecart_pct"] = (comp["ecart_eur"] / comp["budget"]) * 100

    # --- Lisibilité ---
    comp = comp.sort_values(["annee", "groupe_compte"]).reset_index(drop=True)

    return comp
