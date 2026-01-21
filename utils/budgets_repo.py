import pandas as pd


def load_budgets(supabase, annee: int) -> pd.DataFrame:
    res = (
        supabase
        .table("budgets")
        .select("*")
        .eq("annee", annee)
        .execute()
    )
    return pd.DataFrame(res.data)


def save_budgets(supabase, df: pd.DataFrame):
    """
    Sauvegarde robuste :
    - UPSERT sur (annee, compte)
    - Ignore les lignes incomplètes
    """

    if df.empty:
        return

    # Nettoyage minimal
    df = df.copy()

    # Colonnes obligatoires
    required = {"annee", "compte", "budget"}
    missing = required - set(df.columns)
    if missing:
        raise ValueError(f"Colonnes manquantes dans budget : {missing}")

    # Suppression des lignes vides
    df = df.dropna(subset=["compte", "budget"])

    # Normalisation types
    df["annee"] = df["annee"].astype(int)
    df["compte"] = df["compte"].astype(str)
    df["budget"] = df["budget"].astype(float)

    records = df[["annee", "compte", "budget"]].to_dict(orient="records")

    if not records:
        return

    # UPSERT (clé métier)
    supabase.table("budgets").upsert(
        records,
        on_conflict="annee,compte"
    ).execute()