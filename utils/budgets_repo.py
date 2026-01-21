import pandas as pd

def load_budgets(supabase, annee: int) -> pd.DataFrame:
    res = (
        supabase
        .table("budgets")
        .select("annee, compte, budget, groupe_compte")
        .eq("annee", annee)
        .order("compte")
        .execute()
    )
    return pd.DataFrame(res.data)


def save_budgets(supabase, df: pd.DataFrame):
    records = df.to_dict(orient="records")
    (
        supabase
        .table("budgets")
        .upsert(records, on_conflict="annee,compte")
        .execute()
    )
