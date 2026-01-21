import pandas as pd


# =====================================================
# CHARGER LES BUDGETS POUR UNE ANNÉE
# =====================================================
def load_budgets(supabase, annee: int) -> pd.DataFrame:
    """
    Charge les budgets pour une année donnée
    """
    response = (
        supabase
        .table("budgets")
        .select("*")
        .eq("annee", annee)
        .order("compte", desc=False)
        .execute()
    )

    data = response.data or []

    if not data:
        return pd.DataFrame(columns=["id", "annee", "compte", "budget", "groupe_compte"])

    df = pd.DataFrame(data)

    # Typage de sécurité
    df["annee"] = df["annee"].astype(int)
    df["compte"] = df["compte"].astype(str)
    df["budget"] = pd.to_numeric(df["budget"], errors="coerce").fillna(0)

    return df


# =====================================================
# UPSERT (INSERT OU UPDATE) DES BUDGETS
# =====================================================
def upsert_budgets(supabase, df: pd.DataFrame):
    """
    Insère ou met à jour les budgets (clé unique : annee + compte)
    """
    if df.empty:
        return

    records = (
        df[["annee", "compte", "budget", "groupe_compte"]]
        .dropna(subset=["annee", "compte"])
        .to_dict(orient="records")
    )

    if not records:
        return

    supabase.table("budgets").upsert(
        records,
        on_conflict="annee,compte"
    ).execute()


# =====================================================
# SUPPRIMER UN BUDGET
# =====================================================
def delete_budget(supabase, budget_id):
    """
    Supprime un budget par ID
    """
    supabase.table("budgets").delete().eq("id", budget_id).execute()