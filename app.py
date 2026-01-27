import streamlit as st
import pandas as pd
from supabase import create_client
from datetime import date

# =========================
# CONFIG
# =========================
st.set_page_config(page_title="Pilotage des charges", layout="wide")

SUPABASE_URL = st.secrets["SUPABASE_URL"]
SUPABASE_KEY = st.secrets["SUPABASE_ANON_KEY"]

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# =========================
# UTILS
# =========================
def euro(x):
    try:
        return f"{x:,.2f} €".replace(",", " ").replace(".", ",")
    except Exception:
        return "-"

def safe_columns(df, cols):
    """Retourne uniquement les colonnes existantes"""
    return [c for c in cols if c in df.columns]

def load_table(table, filters=None):
    q = supabase.table(table).select("*")
    if filters:
        for k, v in filters.items():
            q = q.eq(k, v)
    res = q.execute()
    return pd.DataFrame(res.data or [])

def load_view(view):
    res = supabase.table(view).select("*").execute()
    return pd.DataFrame(res.data or [])

def facture_url(path):
    if not path:
        return None
    return f"{SUPABASE_URL}/storage/v1/object/public/factures/{path}"

# =========================
# SIDEBAR
# =========================
st.sidebar.title("🏢 Pilotage immeuble")
page = st.sidebar.radio(
    "Navigation",
    [
        "📄 État des dépenses",
        "🚨 Contrôle de répartition",
        "💰 Budget",
        "📊 Budget vs Réel",
    ],
)

annee = st.sidebar.number_input(
    "Année",
    min_value=2020,
    max_value=2100,
    value=date.today().year,
    step=1,
)

# =========================
# PAGE : DÉPENSES
# =========================
if page == "📄 État des dépenses":
    st.title("📄 État des dépenses")

    df = load_table("depenses", {"annee": annee})

    if df.empty:
        st.info("Aucune dépense pour cette année")
    else:
        # lien facture
        if "facture_path" in df.columns:
            df["facture"] = df["facture_path"].apply(facture_url)
        else:
            df["facture"] = None

        cols = safe_columns(
            df,
            [
                "date",
                "poste",
                "groupe_compte",
                "compte",
                "fournisseur",
                "montant_ttc",
                "commentaire",
                "facture",
            ],
        )

        st.dataframe(
            df[cols],
            use_container_width=True,
            column_config={
                "facture": st.column_config.LinkColumn("Facture"),
                "montant_ttc": st.column_config.NumberColumn(
                    "Montant TTC", format="€ %.2f"
                ),
            },
        )

# =========================
# PAGE : CONTRÔLE RÉPARTITION
# =========================
elif page == "🚨 Contrôle de répartition":
    st.title("🚨 Contrôle de répartition")

    df = load_view("v_controle_repartition")

    if df.empty:
        st.success("Toutes les dépenses sont correctement réparties ✅")
    else:
        st.error("Certaines dépenses ne sont PAS réparties à 100 %")

        cols = safe_columns(
            df,
            ["depense_id", "poste", "lots_repartis", "lots_total", "total_quote_part"]
        )
        st.dataframe(df[cols], use_container_width=True)

# =========================
# PAGE : BUDGET
# =========================
elif page == "💰 Budget":
    st.title("💰 Budget")

    df = load_table("budgets", {"annee": annee})

    if df.empty:
        st.warning("Aucun budget défini pour cette année")
    else:
        if "budget" not in df.columns:
            st.error(
                "Colonne 'budget' absente.\n"
                f"Colonnes disponibles : {list(df.columns)}"
            )
        else:
            total_budget = df["budget"].sum()
            st.metric("Budget total", euro(total_budget))

            cols = safe_columns(
                df,
                ["annee", "poste", "groupe_compte", "compte", "budget"]
            )
            st.dataframe(df[cols], use_container_width=True)

# =========================
# PAGE : BUDGET VS RÉEL
# =========================
elif page == "📊 Budget vs Réel":
    st.title("📊 Budget vs Réel")

    df_dep = load_table("depenses", {"annee": annee})
    df_bud = load_table("budgets", {"annee": annee})

    charges_reelles = (
        df_dep["montant_ttc"].sum()
        if "montant_ttc" in df_dep.columns
        else 0
    )

    budget_total = (
        df_bud["budget"].sum()
        if "budget" in df_bud.columns
        else 0
    )

    ecart = budget_total - charges_reelles

    c1, c2, c3 = st.columns(3)
    c1.metric("Charges réelles", euro(charges_reelles))
    c2.metric("Budget", euro(budget_total))
    c3.metric("Écart", euro(ecart))

    st.caption(
        "Données issues exclusivement de Supabase – aucune correction silencieuse."
    )