import streamlit as st
import pandas as pd
from supabase import create_client

# =========================
# CONFIG
# =========================
st.set_page_config(
    page_title="📊 Pilotage des charges",
    layout="wide"
)

SUPABASE_URL = st.secrets["SUPABASE_URL"]
SUPABASE_ANON_KEY = st.secrets["SUPABASE_ANON_KEY"]

supabase = create_client(SUPABASE_URL, SUPABASE_ANON_KEY)


# =========================
# UTILS
# =========================
def euro(val):
    if val is None:
        return "0 €"
    return f"{val:,.2f} €".replace(",", " ").replace(".", ",")


# =========================
# DATA LOADERS (VIEWS ONLY)
# =========================
@st.cache_data
def load_depenses():
    res = supabase.table("v_depenses_detaillees").select("*").execute()
    return pd.DataFrame(res.data)


@st.cache_data
def load_budget_vs_reel():
    res = supabase.table("v_budget_vs_reel").select("*").execute()
    return pd.DataFrame(res.data)


# =========================
# MAIN
# =========================
def main():
    st.title("📊 Pilotage des charges")

    # =========================
    # DEPENSES
    # =========================
    df_dep = load_depenses()

    if df_dep.empty:
        st.warning("Aucune dépense trouvée.")
        return

    total_depenses = df_dep["montant_ttc"].sum()
    nb_depenses = len(df_dep)

    col1, col2 = st.columns(2)
    col1.metric("💸 Total des dépenses", euro(total_depenses))
    col2.metric("🧾 Nombre de dépenses", nb_depenses)

    st.divider()

    # =========================
    # FILTRES
    # =========================
    colf1, colf2, colf3 = st.columns(3)

    with colf1:
        annee = st.selectbox(
            "Année",
            options=sorted(df_dep["annee"].dropna().unique())
        )

    with colf2:
        poste = st.multiselect(
            "Poste",
            options=sorted(df_dep["poste"].dropna().unique())
        )

    with colf3:
        batiment = st.multiselect(
            "Bâtiment",
            options=sorted(df_dep["batiment"].dropna().unique())
        )

    df_filtree = df_dep[df_dep["annee"] == annee]

    if poste:
        df_filtree = df_filtree[df_filtree["poste"].isin(poste)]

    if batiment:
        df_filtree = df_filtree[df_filtree["batiment"].isin(batiment)]

    # =========================
    # TABLE DEPENSES
    # =========================
    st.subheader("📋 Détail des dépenses")

    df_affichage = df_filtree[[
        "date",
        "poste",
        "compte",
        "fournisseur",
        "montant_ttc",
        "batiment",
        "lot",
        "etage",
        "commentaire",
        "facture_url",
        "pdf_url"
    ]].sort_values("date", ascending=False)

    st.dataframe(
        df_affichage,
        use_container_width=True,
        column_config={
            "montant_ttc": st.column_config.NumberColumn(
                "Montant TTC (€)",
                format="%.2f €"
            ),
            "facture_url": st.column_config.LinkColumn("Facture"),
            "pdf_url": st.column_config.LinkColumn("PDF")
        }
    )

    st.divider()

    # =========================
    # BUDGET VS REEL
    # =========================
    st.subheader("💼 Budget vs Réel")

    df_budget = load_budget_vs_reel()
    df_budget = df_budget[df_budget["annee"] == annee]

    st.dataframe(
        df_budget[[
            "groupe_compte",
            "compte",
            "budget",
            "total_reel",
            "ecart"
        ]],
        use_container_width=True,
        column_config={
            "budget": st.column_config.NumberColumn("Budget (€)", format="%.2f €"),
            "total_reel": st.column_config.NumberColumn("Réel (€)", format="%.2f €"),
            "ecart": st.column_config.NumberColumn("Écart (€)", format="%.2f €")
        }
    )


# =========================
# RUN
# =========================
if __name__ == "__main__":
    main()