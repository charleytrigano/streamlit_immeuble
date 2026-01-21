import pandas as pd


def compute_budget_vs_reel(df_bud, df_dep):
    """
    df_bud : budgets d'une année
    df_dep : depenses d'une année
    """

    if df_bud.empty:
        return pd.DataFrame()

    # Sécurité types
    df_bud = df_bud.copy()
    df_dep = df_dep.copy()

    df_bud["compte"] = df_bud["compte"].astype(str)
    df_dep["compte"] = df_dep["compte"].astype(str)

    rows = []

    for _, bud in df_bud.iterrows():
        compte_bud = bud["compte"]

        dep_match = df_dep[
            df_dep["compte"].str.startswith(compte_bud)
        ]

        reel = dep_match["montant_ttc"].sum()

        ecart_eur = reel - bud["budget"]
        ecart_pct = (ecart_eur / bud["budget"] * 100) if bud["budget"] != 0 else 0

        rows.append({
            "groupe_compte": bud.get("groupe_compte"),
            "compte_budget": compte_bud,
            "budget": bud["budget"],
            "reel": reel,
            "ecart_eur": ecart_eur,
            "ecart_pct": ecart_pct,
        })

    return pd.DataFrame(rows)
