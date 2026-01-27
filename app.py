import streamlit as st
import pandas as pd
from supabase import create_client

# =========================
# CONFIG
# =========================
st.set_page_config(
    page_title="Pilotage des charges",
    layout="wide"
)

SUPABASE_URL = st.secrets["SUPABASE_URL"]
SUPABASE_KEY = st.secrets["SUPABASE_ANON_KEY"]

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# =========================
# UTILS
# =========================
def euro(v):
    if pd.isna(v):
        return "—"
    return f"{v:,.2f} €".replace(",", " ").replace(".", ",")

# =========================
# LOADERS
# =========================
@st.cache_data
def load_depenses():
    res = supabase.table("depenses").select("*").execute()
    df = pd.DataFrame(res.data)

    if not df.empty:
        df["date"] = pd.to_datetime(df["date"])
        df["montant_ttc"] = pd.to_numeric(df["montant_ttc"], errors="coerce")
        df["lot_id"] = pd.to_numeric(df["lot_id"], errors="coerce")

    return df


@st.cache_data
def load_lots():
    res = supabase.table("lots").select("*").execute()
    df = pd.DataFrame(res.data)

    if not df.empty:
        df["id"] = pd.to_numeric(df["id"], errors="coerce")

    return df


@st.cache_data
def load_budgets():
    res = supabase.table("budgets").select("*").execute()
    df = pd.DataFrame(res.data)

    if not df.empty:
        df["annee"] = pd.to_numeric(df["annee"], errors="coerce")
        df["budget"] = pd.to_numeric(df["budget"], errors="coerce")

    return df

# =========================
# MAIN
# =========================
def main():
    st.title("📊 Pilotage des charges")

    df_dep = load_depenses()
    df_lots = load_lots()
    df_budget = load_budgets()

    # =========================
    # METRICS
    # =========================
    col1, col2 = st.columns(2)

    col1.metric(
        "💸 Total des dépenses",
        euro(df_dep["montant_ttc"].sum())
    )

    col2.metric(
        "🧾 Nombre de dépenses",
        int(len(df_dep))
    )

    # =========================
    # TABS
    # =========================
    tab1, tab2, tab3, tab4 = st.tabs([
        "📋 Dépenses",
        "📈 Budget vs Réel",
        "🏢 Lots",
        "📎 Pièces"
    ])

    # =========================
    # TAB 1 — DEPENSES
    # =========================
    with tab1:
        df_display = df_dep.merge(
            df_lots,
            left_on="lot_id",
            right_on="id",
            how="left"
        )

        df_display = df_display[[
            "date",
            "poste",
            "compte",
            "fournisseur",
            "montant_ttc",
            "lot",
            "batiment",
            "etage",
            "commentaire"
        ]].sort_values("date", ascending=False)

        df_display["montant_ttc"] = df_display["montant_ttc"].apply(euro)

        st.dataframe(
            df_display,
            use_container_width=True,
            hide_index=True
        )

    # =========================
    # TAB 2 — BUDGET VS REEL
    # =========================
    with tab2:
        df_dep["annee"] = df_dep["date"].dt.year

        df_reel = (
            df_dep
            .groupby(["annee", "poste"], as_index=False)["montant_ttc"]
            .sum()
            .rename(columns={"montant_ttc": "reel"})
        )

        df_compare = df_reel.merge(
            df_budget,
            on=["annee", "poste"],
            how="left"
        )

        df_compare["budget"] = df_compare["budget"].fillna(0)
        df_compare["ecart"] = df_compare["budget"] - df_compare["reel"]

        df_compare = df_compare.sort_values(
            ["annee", "poste"]
        )

        df_show = df_compare.copy()
        df_show["budget"] = df_show["budget"].apply(euro)
        df_show["reel"] = df_show["reel"].apply(euro)
        df_show["ecart"] = df_show["ecart"].apply(euro)

        st.dataframe(
            df_show,
            use_container_width=True,
            hide_index=True
        )

    # =========================
    # TAB 3 — LOTS
    # =========================
    with tab3:
        st.dataframe(
            df_lots,
            use_container_width=True,
            hide_index=True
        )

    # =========================
    # TAB 4 — PIECES
    # =========================
    with tab4:
        pieces = df_dep[[
            "date",
            "poste",
            "fournisseur",
            "montant_ttc",
            "pdf_url",
            "facture_url"
        ]].copy()

        pieces["montant_ttc"] = pieces["montant_ttc"].apply(euro)

        st.dataframe(
            pieces,
            use_container_width=True,
            hide_index=True
        )


if __name__ == "__main__":
    main()