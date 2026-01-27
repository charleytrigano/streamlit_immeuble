import streamlit as st
import pandas as pd
from supabase import create_client

# =========================
# CONFIG
# =========================
st.set_page_config(page_title="Pilotage des charges", layout="wide")

SUPABASE_URL = st.secrets["SUPABASE_URL"]
SUPABASE_KEY = st.secrets["SUPABASE_ANON_KEY"]
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

def euro(x):
    if pd.isna(x):
        return "0 €"
    return f"{x:,.2f} €".replace(",", " ").replace(".", ",")

# =========================
# DATA LOADING
# =========================
@st.cache_data
def load_depenses():
    data = supabase.table("depenses").select("*").execute().data
    df = pd.DataFrame(data)

    if df.empty:
        return df

    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    df["annee"] = df["annee"].fillna(df["date"].dt.year)
    df["montant_ttc"] = pd.to_numeric(df["montant_ttc"], errors="coerce").fillna(0)

    return df

@st.cache_data
def load_budgets():
    data = supabase.table("budgets").select("*").execute().data
    df = pd.DataFrame(data)

    if df.empty:
        return df

    df["budget"] = pd.to_numeric(df["budget"], errors="coerce").fillna(0)
    return df

# =========================
# MAIN
# =========================
def main():
    st.title("📊 Pilotage des charges")

    df_dep = load_depenses()
    df_bud = load_budgets()

    if df_dep.empty:
        st.warning("Aucune dépense trouvée.")
        return

    # =========================
    # FILTRES
    # =========================
    st.sidebar.header("🔎 Filtres")

    annees = sorted(df_dep["annee"].dropna().unique())
    annee = st.sidebar.selectbox("Année", ["Toutes"] + annees)

    comptes = sorted(df_dep["compte"].dropna().unique())
    compte = st.sidebar.multiselect("Compte", comptes)

    fournisseurs = sorted(df_dep["fournisseur"].dropna().unique())
    fournisseur = st.sidebar.multiselect("Fournisseur", fournisseurs)

    postes = sorted(df_dep["poste"].dropna().unique())
    poste = st.sidebar.multiselect("Poste", postes)

    df = df_dep.copy()

    if annee != "Toutes":
        df = df[df["annee"] == annee]
    if compte:
        df = df[df["compte"].isin(compte)]
    if fournisseur:
        df = df[df["fournisseur"].isin(fournisseur)]
    if poste:
        df = df[df["poste"].isin(poste)]

    # =========================
    # KPI
    # =========================
    c1, c2, c3 = st.columns(3)
    c1.metric("💸 Total des dépenses", euro(df["montant_ttc"].sum()))
    c2.metric("🧾 Nombre de lignes", len(df))
    c3.metric("📉 Dépense moyenne", euro(df["montant_ttc"].mean()))

    # =========================
    # TABS
    # =========================
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "📄 État des dépenses",
        "💰 Budget",
        "📊 Budget vs Réel",
        "📈 Statistiques",
        "✅ Contrôle répartition"
    ])

    # =========================
    # TAB 1 – ÉTAT DES DÉPENSES
    # =========================
    with tab1:
        st.subheader("📄 État des dépenses")

        st.dataframe(
            df[[
                "date",
                "poste",
                "compte",
                "fournisseur",
                "montant_ttc"
            ]].sort_values("date", ascending=False),
            use_container_width=True
        )

    # =========================
    # TAB 2 – BUDGET
    # =========================
    with tab2:
        st.subheader("💰 Budgets")

        if df_bud.empty:
            st.info("Aucun budget disponible.")
        else:
            st.dataframe(df_bud, use_container_width=True)

    # =========================
    # TAB 3 – BUDGET VS RÉEL
    # =========================
    with tab3:
        st.subheader("📊 Budget vs Réel")

        if df_bud.empty:
            st.warning("Pas de budgets pour comparaison.")
        else:
            dep_group = (
                df.groupby(["annee", "compte"])
                .agg(reel=("montant_ttc", "sum"))
                .reset_index()
            )

            bud_group = (
                df_bud.groupby(["annee", "compte"])
                .agg(budget=("budget", "sum"))
                .reset_index()
            )

            comp = dep_group.merge(
                bud_group,
                on=["annee", "compte"],
                how="left"
            )

            comp["budget"] = comp["budget"].fillna(0)
            comp["ecart"] = comp["reel"] - comp["budget"]

            st.dataframe(comp, use_container_width=True)

    # =========================
    # TAB 4 – STATISTIQUES
    # =========================
    with tab4:
        st.subheader("📈 Statistiques")

        by_poste = (
            df.groupby("poste")
            .agg(total=("montant_ttc", "sum"))
            .sort_values("total", ascending=False)
        )

        st.bar_chart(by_poste)

    # =========================
    # TAB 5 – CONTRÔLE RÉPARTITION
    # =========================
    with tab5:
        st.subheader("✅ Contrôle de répartition")

        controle = df[df["repartition_requise"] == True]

        if controle.empty:
            st.success("Aucune anomalie détectée.")
        else:
            st.warning("Dépenses nécessitant une répartition")
            st.dataframe(controle, use_container_width=True)

# =========================
# RUN
# =========================
if __name__ == "__main__":
    main()