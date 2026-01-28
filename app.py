import streamlit as st
import pandas as pd
from supabase import create_client

# =========================
# CONFIG
# =========================
st.set_page_config(page_title="Pilotage des charges", layout="wide")

SUPABASE_URL = st.secrets["SUPABASE_URL"]
SUPABASE_ANON_KEY = st.secrets["SUPABASE_ANON_KEY"]
supabase = create_client(SUPABASE_URL, SUPABASE_ANON_KEY)

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

budget_total = (
    df_bud_y["budget"].sum()
    if "budget" in df_bud_y.columns and not df_bud_y.empty
    else 0
)

ecart = budget_total - total_dep

c1, c2, c3 = st.columns(3)
c1.metric("💸 Dépenses réelles", euro(total_dep))
c2.metric("💰 Budget total", euro(budget_total))
c3.metric("📊 Écart", euro(ecart))

# =========================
# TABS
# =========================
tab1, tab2, tab3 = st.tabs([
    "📄 État des dépenses",
    "📚 Plan comptable",
    "💰 Budget"
])

# =========================
# TAB 1 — DEPENSES (LOCKED)
# =========================
with tab1:
    st.subheader("📄 État des dépenses (verrouillé)")

    cols = [
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

    cols = [c for c in cols if c in df_dep_y.columns]

    st.dataframe(
        df_dep_y[cols].sort_values("date"),
        use_container_width=True
    )

# =========================
# TAB 2 — PLAN COMPTABLE (LOCKED)
# =========================
with tab2:
    st.subheader("📚 Plan comptable (verrouillé)")
    st.dataframe(
        df_plan.sort_values(["groupe_compte", "compte_8"]),
        use_container_width=True
    )

# =========================
# TAB 3 — BUDGET
# =========================
with tab3:
    st.subheader("💰 Budget par groupe")

    # ⚠️ SÉLECTION SÉCURISÉE DES COLONNES
    bud_cols = ["groupe_compte", "libelle_groupe", "budget"]
    bud_cols = [c for c in bud_cols if c in df_bud_y.columns]

    if df_bud_y.empty or not bud_cols:
        st.warning("Aucun budget enregistré pour cette année.")
    else:
        st.dataframe(
            df_bud_y[bud_cols].sort_values("groupe_compte"),
            use_container_width=True
        )

    st.metric("Total budget", euro(budget_total))

    st.divider()

    # ===== FORM ADD / UPDATE =====
    st.subheader("➕ Ajouter / Modifier un budget")

    with st.form("budget_form"):
        groupe = st.text_input("Groupe de compte (ex : 601)")
        libelle_grp = st.text_input("Libellé du groupe (ex : Eau)")
        montant = st.number_input("Budget (€)", min_value=0.0)

        if st.form_submit_button("Enregistrer"):
            supabase.table("budgets").upsert({
                "annee": annee_sel,
                "groupe_compte": groupe,
                "libelle_groupe": libelle_grp,
                "budget": montant
            }).execute()
            st.success("Budget enregistré")
            st.rerun()

    st.divider()

    # ===== DELETE =====
    if not df_bud_y.empty and "groupe_compte" in df_bud_y.columns:
        grp_del = st.selectbox(
            "Groupe à supprimer",
            df_bud_y["groupe_compte"].unique()
        )

        if st.button("Supprimer"):
            supabase.table("budgets") \
                .delete() \
                .eq("annee", annee_sel) \
                .eq("groupe_compte", grp_del) \
                .execute()
            st.success("Budget supprimé")
            st.rerun()