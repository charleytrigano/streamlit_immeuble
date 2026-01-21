import pandas as pd


# =====================================================
# LECTURE DES DÉPENSES
# =====================================================
def load_depenses(supabase, annee: int) -> pd.DataFrame:
    """
    Charge les dépenses pour une année donnée
    """
    response = (
        supabase
        .table("depenses")
        .select("*")
        .eq("annee", annee)
        .order("date", desc=False)
        .execute()
    )

    data = response.data or []

    if not data:
        return pd.DataFrame()

    df = pd.DataFrame(data)

    # Sécurités de typage
    if "date" in df.columns:
        df["date"] = pd.to_datetime(df["date"]).dt.date

    if "montant_ttc" in df.columns:
        df["montant_ttc"] = pd.to_numeric(df["montant_ttc"], errors="coerce").fillna(0)

    return df


# =====================================================
# INSERTION D’UNE DÉPENSE
# =====================================================
def insert_depense(supabase, depense: dict):
    """
    Insère une nouvelle dépense
    """
    supabase.table("depenses").insert(depense).execute()


# =====================================================
# SUPPRESSION D’UNE DÉPENSE
# =====================================================
def delete_depense(supabase, depense_id):
    """
    Supprime une dépense par son ID
    """
    supabase.table("depenses").delete().eq("id", depense_id).execute()