import pandas as pd


REQUIRED_DEP_COLS = {"annee", "compte", "montant_ttc"}
REQUIRED_BUD_COLS = {"annee", "compte", "budget"}


def _check_columns(df: pd.DataFrame, required: set, df_name: str):
    missing = required - set(df.columns)
    if missing:
        raise ValueError(
            f"[{df_name}] Colonnes manquantes : {missing}. "
            f"Colonnes reçues : {df.columns.tolist()}"
        )


def compute_budget_vs_reel(df_bud: pd.DataFrame, df_dep: pd.DataFrame) -> pd.DataFrame:
    """
    Compare budget vs dépenses réelles par compte et par année.
    Compatible Supabase / PostgreSQL.
    """

    # =========================
    # VALIDATIONS
    # =========================
    if df_bud.empty:
        raise ValueError("df_bud est vide")
    if df_dep.empty:
        raise ValueError("df_dep est vide")

    _check_columns(df_bud, REQUIRED_BUD_COLS, "Budgets")
    _check_columns(df_dep, REQUIRED_DEP_COLS, "Dépenses")

    # =========================
    # NORMALISATION DES TYPES
    # =========================
    df_bud = df_bud.copy()
    df_dep = df_dep.copy()

    df_bud["annee"] = df_bud["annee"].astype(int)
    df_dep["annee"] = df_dep["annee"].astype(int)

    df_bud["compte"] = df_bud["compte"].astype(str)
    df_dep["compte"] = df_dep["compte"].astype(str)

    df_bud["budget"] = pd.to_numeric(df_bud["budget"], errors="coerce").fillna(0)
    df_dep["montant_ttc"] = pd.to_numeric(df_dep["montant_ttc"], errors="coerce").fillna(0)

    # =========================
    # AGRÉGATION DES DÉPENSES
    # =========================
    dep_agg = (
        df_dep
        .groupby(["annee", "compte"], as_index=False)
        .agg(depense_reelle=("montant_ttc", "sum"))
    )

    # =========================
    # AGRÉGATION DES BUDGETS
    # =========================
    bud_agg = (
        df_bud
        .groupby(["annee", "compte"], as_index=False)
        .agg(budget=("budget", "sum"))
    )

    # =========================
    # FUSION BUDGET / RÉEL
    # =========================
    df_comp = pd.merge(
        bud_agg,
        dep_agg,
        on=["annee", "compte"],
        how="left",
    )

    df_comp["depense_reelle"] = df_comp["depense_reelle"].fillna(0)

    # =========================
    # CALCULS
    # =========================
    df_comp["ecart"] = df_comp["budget"] - df_comp["depense_reelle"]

    df_comp["taux_realisation"] = (
        df_comp["depense_reelle"] / df_comp["budget"]
    ).replace([float("inf"), -float("inf")], 0)

    df_comp["taux_realisation"] = (
        df_comp["taux_realisation"].fillna(0).round(2)
    )

    # =========================
    # TRI & SORTIE
    # =========================
    df_comp = df_comp.sort_values(
        by=["annee", "compte"], ascending=[False, True]
    )

    return df_comp
