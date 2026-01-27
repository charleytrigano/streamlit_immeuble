import streamlit as st
import pandas as pd
from supabase import create_client

# =====================================================
# CONFIG
# =====================================================
st.set_page_config(page_title="Pilotage des charges", layout="wide")

SUPABASE_URL = st.secrets["SUPABASE_URL"]
SUPABASE_KEY = st.secrets["SUPABASE_ANON_KEY"]

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# =====================================================
# UTILS
# =====================================================
def euro(v):
    if pd.isna(v):
        return "—"
    return f"{v:,.2f} €".replace(",", " ").replace(".", ",")

def safe_col(df, col):
    if col not in df.columns:
        df[col] = None
    return df

# =====================================================
# LOADERS
# =====================================================
@st.cache_data
def load_depenses():
    res = supabase.table("depenses").select("*").execute()
    df = pd.DataFrame(res.data)

    if df.empty:
        return df

    df["date"] = pd.to_datetime(df.get("date"), errors="coerce")
    df["montant_ttc"] = pd.to_numeric(df.get("montant_ttc"), errors="coerce")
    df["lot_id"] = pd.to_numeric(df.get("lot_id"), errors="coerce")

    for c in ["poste", "compte", "fournisseur", "commentaire", "pdf_url"]:
        df = safe_col(df, c)

    return df


@st.cache_data
def load_lots():
    res = supabase.table("lots").select("*").execute()
    df = pd.DataFrame(res.data)

    if df.empty:
        return df

    df["lot_id"] = pd.to_numeric(df.get("lot_id"), errors="coerce")

    for c in ["lot", "batiment", "etage", "tantiemes"]:
        df = safe_col(df, c)

    return df


@st.cache_data
def load_budgets():
    res = supabase.table("budgets").select("*").execute()
    df = pd.DataFrame(res.data)

    if df.empty:
        return df

    df["annee"] = pd.to_numeric(df.get("annee"), errors="coerce")
    df["budget"] = pd.to_numeric(df.get("budget"), errors="coerce")
    df = safe_col(df, "poste")

    return df

# =====================================================
# MAIN
# =====================================================
def main():
    st.title("📊 Pilotage des charges")

    df_dep = load_depenses()
    df_lots = load_lots()
    df_budget = load_budgets()

    # =================================================
    # KPI GLOBALS
    # =================================================
    c1, c2 = st.columns(2)
    c1.metric("💸 Total des dépenses", euro(df_dep["montant_ttc"].sum()))
    c2.metric("🧾 Nombre de dépenses", len(df_dep))

    # =================================================
    # TABS
    # =================================================
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "📋 État des dépenses",
        "💰 Budget",
        "📊 Budget vs Réel",
        "📈 Statistiques",
        "🚨 Contrôle répartition"
    ])

    # =================================================
    # TAB 1 — ÉTAT DES DÉPENSES
    # =================================================
    with tab1:
        df_show = df_dep.merge(
            df_lots,
            on="lot_id",
            how="left"
        )

        df_show["montant_ttc"] = df_show["montant_ttc"].apply(euro)

        st.dataframe(
            df_show[[
                "date",
                "poste",
                "compte",
                "fournisseur",
                "montant_ttc",
                "lot",
                "batiment",
                "etage",
                "commentaire",
                "pdf_url"
            ]],
            use_container_width=True,
            hide_index=True
        )

    # =================================================
    # TAB 2 — BUDGET
    # =================================================
    with tab2:
        df_b = df_budget.copy()
        df_b["budget"] = df_b["budget"].apply(euro)

        st.dataframe(df_b, use_container_width=True, hide_index=True)

    # =================================================
    # TAB 3 — BUDGET VS RÉEL
    # =================================================
    with tab3:
        df_dep["annee"] = df_dep["date"].dt.year

        df_reel = (
            df_dep
            .groupby(["annee", "poste"], as_index=False)["montant_ttc"]
            .sum()
            .rename(columns={"montant_ttc": "reel"})
        )

        df_cmp = df_reel.merge(
            df_budget,
            on=["annee", "poste"],
            how="left"
        )

        df_cmp["budget"] = df_cmp["budget"].fillna(0)
        df_cmp["ecart"] = df_cmp["budget"] - df_cmp["reel"]

        df_cmp["budget"] = df_cmp["budget"].apply(euro)
        df_cmp["reel"] = df_cmp["reel"].apply(euro)
        df_cmp["ecart"] = df_cmp["ecart"].apply(euro)

        st.dataframe(df_cmp, use_container_width=True, hide_index=True)

    # =================================================
    # TAB 4 — STATISTIQUES
    # =================================================
    with tab4:
        stats = (
            df_dep
            .groupby("poste", as_index=False)["montant_ttc"]
            .sum()
            .sort_values("montant_ttc", ascending=False)
        )

        stats["montant_ttc"] = stats["montant_ttc"].apply(euro)
        st.dataframe(stats, use_container_width=True, hide_index=True)

    # =================================================
    # TAB 5 — CONTRÔLE RÉPARTITION
    # =================================================
    with tab5:
        st.info(
            "Contrôle logique : la somme des charges par poste doit "
            "correspondre au total des dépenses."
        )

        total = df_dep["montant_ttc"].sum()
        check = (
            df_dep.groupby("poste")["montant_ttc"].sum().sum()
        )

        st.metric("Total dépenses", euro(total))
        st.metric("Somme par postes", euro(check))
        st.metric("Écart", euro(total - check))


if __name__ == "__main__":
    main()