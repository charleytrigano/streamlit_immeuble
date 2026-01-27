import streamlit as st
import pandas as pd
from supabase import create_client

# =========================
# CONFIG
# =========================
st.set_page_config(page_title="Pilotage des charges", layout="wide")

# =========================
# SUPABASE
# =========================
@st.cache_resource
def get_supabase():
    return create_client(
        st.secrets["SUPABASE_URL"],
        st.secrets["SUPABASE_ANON_KEY"]
    )

supabase = get_supabase()

def euro(x):
    return f"{x:,.2f} €".replace(",", " ").replace(".", ",")

# =========================
# DATA LOADERS
# =========================
@st.cache_data
def load_depenses():
    return pd.DataFrame(
        supabase.table("depenses")
        .select("*")
        .execute()
        .data
    )

@st.cache_data
def load_budget():
    return pd.DataFrame(
        supabase.table("budget")
        .select("*")
        .execute()
        .data
    )

# =========================
# APP
# =========================
def main():
    st.title("📊 Pilotage des charges")

    df_dep = load_depenses()
    df_bud = load_budget()

    if df_dep.empty:
        st.error("Aucune dépense trouvée")
        return

    # =========================
    # FILTRES GLOBAUX
    # =========================
    st.sidebar.header("🔎 Filtres")

    annee = st.sidebar.selectbox(
        "Année",
        sorted(df_dep["annee"].dropna().unique())
    )

    df_dep = df_dep[df_dep["annee"] == annee]
    df_bud = df_bud[df_bud["annee"] == annee]

    compte = st.sidebar.selectbox(
        "Compte",
        ["Tous"] + sorted(df_dep["compte"].dropna().unique())
    )
    fournisseur = st.sidebar.selectbox(
        "Fournisseur",
        ["Tous"] + sorted(df_dep["fournisseur"].dropna().unique())
    )
    poste = st.sidebar.selectbox(
        "Poste",
        ["Tous"] + sorted(df_dep["poste"].dropna().unique())
    )

    if compte != "Tous":
        df_dep = df_dep[df_dep["compte"] == compte]
    if fournisseur != "Tous":
        df_dep = df_dep[df_dep["fournisseur"] == fournisseur]
    if poste != "Tous":
        df_dep = df_dep[df_dep["poste"] == poste]

    # =========================
    # ONGLET
    # =========================
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "📄 État des dépenses",
        "💰 Budget",
        "📊 Budget vs Réel",
        "📈 Statistiques",
        "✅ Contrôle répartition"
    ])

    # =========================
    # 1. ÉTAT DES DÉPENSES
    # =========================
    with tab1:
        st.subheader("📄 État des dépenses")

        col1, col2, col3 = st.columns(3)
        col1.metric("Total dépenses", euro(df_dep["montant_ttc"].sum()))
        col2.metric("Nombre de lignes", len(df_dep))
        col3.metric("Dépense moyenne", euro(df_dep["montant_ttc"].mean()))

        display_cols = [
            "date", "compte", "poste", "fournisseur",
            "montant_ttc", "commentaire"
        ]

        if "facture_url" in df_dep.columns:
            df_dep["Facture"] = df_dep["facture_url"].apply(
                lambda x: f"[📄 Voir]({x})" if pd.notna(x) else ""
            )
            display_cols.append("Facture")

        st.dataframe(
            df_dep[display_cols],
            use_container_width=True
        )

    # =========================
    # 2. BUDGET
    # =========================
    with tab2:
        st.subheader("💰 Budget")

        if df_bud.empty:
            st.warning("Aucun budget pour cette année")
        else:
            st.metric("Budget total", euro(df_bud["budget"].sum()))
            st.dataframe(df_bud, use_container_width=True)

    # =========================
    # 3. BUDGET VS RÉEL
    # =========================
    with tab3:
        st.subheader("📊 Budget vs Réel")

        dep_agg = (
            df_dep
            .groupby("compte", as_index=False)
            .agg(reel=("montant_ttc", "sum"))
        )

        bvr = dep_agg.merge(
            df_bud[["compte", "budget"]],
            on="compte",
            how="outer"
        ).fillna(0)

        bvr["écart"] = bvr["reel"] - bvr["budget"]

        col1, col2, col3 = st.columns(3)
        col1.metric("Réel", euro(bvr["reel"].sum()))
        col2.metric("Budget", euro(bvr["budget"].sum()))
        col3.metric("Écart", euro(bvr["écart"].sum()))

        st.dataframe(
            bvr.rename(columns={
                "compte": "Compte",
                "reel": "Réel (€)",
                "budget": "Budget (€)",
                "écart": "Écart (€)"
            }),
            use_container_width=True
        )

    # =========================
    # 4. STATISTIQUES
    # =========================
    with tab4:
        st.subheader("📈 Statistiques")

        st.markdown("### Par poste")
        st.dataframe(
            df_dep.groupby("poste", as_index=False)
            .agg(total=("montant_ttc", "sum"))
            .sort_values("total", ascending=False),
            use_container_width=True
        )

        st.markdown("### Par fournisseur")
        st.dataframe(
            df_dep.groupby("fournisseur", as_index=False)
            .agg(total=("montant_ttc", "sum"))
            .sort_values("total", ascending=False),
            use_container_width=True
        )

    # =========================
    # 5. CONTRÔLE RÉPARTITION
    # =========================
    with tab5:
        st.subheader("✅ Contrôle simple")

        total_dep = df_dep["montant_ttc"].sum()
        total_budget = df_bud["budget"].sum() if not df_bud.empty else 0

        st.metric("Total dépenses", euro(total_dep))
        st.metric("Total budget", euro(total_budget))
        st.metric("Différence", euro(total_dep - total_budget))


# =========================
# RUN
# =========================
if __name__ == "__main__":
    main()