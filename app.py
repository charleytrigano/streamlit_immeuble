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
SUPABASE_KEY = st.secrets["SUPABASE_KEY"]
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# =========================
# HELPERS
# =========================
@st.cache_data
def load_table(name):
    res = supabase.table(name).select("*").execute()
    return pd.DataFrame(res.data)

def euro(x):
    return f"{x:,.2f} €".replace(",", " ").replace(".", ",")

# =========================
# LOAD DATA
# =========================
df_dep = load_table("depenses")
df_plan = load_table("plan_comptable")
df_bud = load_table("budgets")

# =========================
# CLEAN PLAN COMPTABLE
# =========================
df_plan = df_plan[
    (df_plan["compte_8"].notna()) &
    (df_plan["compte_8"] != "EMPTY") &
    (df_plan["libelle_groupe"] != "000")
]

# =========================
# ENRICH DEPENSES
# =========================
df_dep = df_dep.merge(
    df_plan,
    left_on="compte",
    right_on="compte_8",
    how="left"
)

# =========================
# SIDEBAR
# =========================
st.sidebar.title("🔎 Filtres")

annees = sorted(df_dep["annee"].dropna().unique())
annee_sel = st.sidebar.selectbox("Année", annees)

df_dep_y = df_dep[df_dep["annee"] == annee_sel]
df_bud_y = df_bud[df_bud["annee"] == annee_sel]

# =========================
# KPI
# =========================
total_dep = df_dep_y["montant_ttc"].sum()

bud_total = (
    df_bud_y["montant"].sum()
    if "montant" in df_bud_y.columns
    else 0
)

ecart = bud_total - total_dep

c1, c2, c3 = st.columns(3)
c1.metric("💸 Dépenses réelles", euro(total_dep))
c2.metric("💰 Budget", euro(bud_total))
c3.metric("📊 Écart", euro(ecart))

# =========================
# TABS
# =========================
tab1, tab2, tab3 = st.tabs([
    "📄 État des dépenses",
    "📚 Plan comptable (verrouillé)",
    "💰 Budget"
])

# =========================
# TAB 1 — DEPENSES (LOCKED)
# =========================
with tab1:
    st.subheader("📄 État des dépenses (lecture seule)")

    cols_order = [
        "date",
        "annee",
        "compte",
        "libelle",
        "groupe_compte",
        "libelle_groupe",
        "fournisseur",
        "montant_ttc",
        "commentaire"
    ]

    cols_existing = [c for c in cols_order if c in df_dep_y.columns]

    st.dataframe(
        df_dep_y[cols_existing].sort_values("date"),
        use_container_width=True
    )

# =========================
# TAB 2 — PLAN COMPTABLE (LOCKED)
# =========================
with tab2:
    st.subheader("📚 Plan comptable (verrouillé)")

    st.info(
        "Le plan comptable est verrouillé.\n\n"
        "Les comptes invalides (EMPTY / groupe 000) ont été automatiquement supprimés."
    )

    st.dataframe(
        df_plan.sort_values(["groupe_compte", "compte_8"]),
        use_container_width=True
    )

# =========================
# TAB 3 — BUDGET (CRUD)
# =========================
with tab3:
    st.subheader("💰 Gestion du budget")

    st.dataframe(
        df_bud_y.sort_values("groupe_compte"),
        use_container_width=True
    )

    st.divider()
    st.subheader("➕ Ajouter / Modifier un budget")

    with st.form("budget_form"):
        groupe = st.text_input("Groupe de compte (ex: 601)")
        montant = st.number_input("Montant (€)", min_value=0.0)
        submitted = st.form_submit_button("Enregistrer")

        if submitted:
            supabase.table("budgets").upsert({
                "annee": annee_sel,
                "groupe_compte": groupe,
                "montant": montant
            }).execute()

            st.success("Budget enregistré")
            st.rerun()

    st.divider()
    st.subheader("🗑️ Supprimer un budget")

    grp_del = st.selectbox(
        "Groupe à supprimer",
        df_bud_y["groupe_compte"].unique()
        if not df_bud_y.empty else []
    )

    if st.button("Supprimer"):
        supabase.table("budgets") \
            .delete() \
            .eq("annee", annee_sel) \
            .eq("groupe_compte", grp_del) \
            .execute()

        st.success("Budget supprimé")
        st.rerun()