import pandas as pd

def load_depenses(supabase, annee: int) -> pd.DataFrame:
    res = (
        supabase
        .table("depenses")
        .select("*")
        .eq("annee", annee)
        .order("date", desc=False)
        .execute()
    )
    return pd.DataFrame(res.data)