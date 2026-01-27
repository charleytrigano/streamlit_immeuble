import streamlit as st
import pandas as pd
from supabase import create_client

# ======================
# CONFIG
# ======================
st.set_page_config(
    page_title="Pilotage des charges",
    layout="wide"
)

# ======================
# SUPABASE
# ======================
@st.cache_resource
def get_supabase():
    return create_client(
        st.secrets["SUPABASE_URL"],
        st.secrets["SUPABASE_ANON_KEY"]
    )

supabase = get_supabase()

# ======================
# UTILS
# ======================
def euro(v):
    return f"{v:,.2f} €".replace(",", " ").replace(".", ",")

def load_table(name):
    return pd.DataFrame(
        supabase.table(name).select("*").execute().data
    )

# ======================
# SIDEBAR
# ======================
st.sidebar.title("🔎 Filtres")

annee = st.sidebar.selectbox(
    "Année",
    [2025],  # volontairement verrouillé tant que tu veux du propre
    index=0
)

onglet = st.sidebar.radio(
    "Navigation",
    [
        "📄 État des dépenses",
        "📘 Plan comptable",
        "💰 Budget",
        "📊 Budget vs Réel"
    ]
)

# ======================
# CHARGEMENT DONNÉES
# ======================
df_dep = load_table("depenses")
df_plan = load_table("plan_comptable")
df_bud = load_table("budgets")

df_dep = df_dep[df_dep["annee"] == annee]

# ======================
# ONGLET 1 — ÉTAT DES DÉPENSES
# ======================
if onglet == "📄 État des dépenses":

    st.title("📄 État des dépenses")

    df_disp = (
        df_dep
        .merge(
            df_plan,
            left_on="compte",
            right_on="compte_8",
            how="left"
        )
    )

    col1, col2, col3 = st.columns(3)
    col1.metric("Total dépenses", euro(df_disp["montant_ttc"].sum()))
    col2.metric("Nombre de lignes", len(df_disp))
    col3.metric(
        "Dépense moyenne",
        euro(df_disp["montant_ttc"].mean()) if len(df_disp) else "0 €"
    )

    st.dataframe(
        df_disp[[
            "annee",
            "compte",
            "libelle_compte",
            "groupe_compte",
            "libelle_groupe",
            "poste",
            "fournisseur",
            "montant_ttc",
            "commentaire"
        ]],
        use_container_width=True
    )

# ======================
# ONGLET 2 — PLAN COMPTABLE
# ======================
elif onglet == "📘 Plan comptable":

    st.title("📘 Plan comptable")

    st.dataframe(
        df_plan.sort_values(["groupe_compte", "compte_8"]),
        use_container_width=True
    )

    st.subheader("✏️ Modifier le libellé d’un groupe")

    grp = st.selectbox(
        "Groupe de compte",
        sorted(df_plan["groupe_compte"].unique())
    )

    libelle_actuel = (
        df_plan[df_plan["groupe_compte"] == grp]
        ["libelle_groupe"]
        .iloc[0]
    )

    nouveau = st.text_input(
        "Libellé groupe",
        value=libelle_actuel
    )

    if st.button("💾 Enregistrer"):
        supabase.table("plan_comptable") \
            .update({"libelle_groupe": nouveau}) \
            .eq("groupe_compte", grp) \
            .execute()

        st.success("Libellé mis à jour")
        st.experimental_rerun()

# ======================
# ONGLET 3 — BUDGET
# ======================
elif onglet == "💰 Budget":

    st.title("💰 Budget")

    df_bud_y = df_bud[df_bud["annee"] == annee]

    st.metric(
        "Budget total",
        euro(df_bud_y["montant"].sum())
    )

    st.dataframe(
        df_bud_y.merge(
            df_plan[["groupe_compte", "libelle_groupe"]].drop_duplicates(),
            on="groupe_compte",
            how="left"
        ).sort_values("groupe_compte"),
        use_container_width=True
    )

# ======================
# ONGLET 4 — BUDGET VS RÉEL
# ======================
elif onglet == "📊 Budget vs Réel":

    st.title("📊 Budget vs Réel — par groupe de comptes")

    # Dépenses par groupe
    df_dep_grp = (
        df_dep
        .merge(
            df_plan[["compte_8", "groupe_compte", "libelle_groupe"]],
            left_on="compte",
            right_on="compte_8",
            how="left"
        )
        .groupby(["groupe_compte", "libelle_groupe"], as_index=False)
        .agg(depenses=("montant_ttc", "sum"))
    )

    # Budget par groupe
    df_bud_grp = (
        df_bud[df_bud["annee"] == annee]
        .groupby("groupe_compte", as_index=False)
        .agg(budget=("montant", "sum"))
    )

    # Fusion
    df_kpi = (
        df_dep_grp
        .merge(df_bud_grp, on="groupe_compte", how="left")
        .fillna(0)
    )

    df_kpi["ecart"] = df_kpi["budget"] - df_kpi["depenses"]
    df_kpi["taux"] = df_kpi.apply(
        lambda r: (r["depenses"] / r["budget"] * 100) if r["budget"] > 0 else 0,
        axis=1
    )

    col1, col2, col3 = st.columns(3)
    col1.metric("Dépenses", euro(df_kpi["depenses"].sum()))
    col2.metric("Budget", euro(df_kpi["budget"].sum()))
    col3.metric("Écart global", euro(df_kpi["ecart"].sum()))

    st.dataframe(
        df_kpi.sort_values("groupe_compte"),
        use_container_width=True
    )
