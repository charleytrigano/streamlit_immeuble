import streamlit as st
import pandas as pd
from supabase import create_client

# ---------------- CONFIG ----------------
st.set_page_config(page_title="Pilotage des charges", layout="wide")

SUPABASE_URL = st.secrets["SUPABASE_URL"]
SUPABASE_ANON_KEY = st.secrets["SUPABASE_ANON_KEY"]

supabase = create_client(SUPABASE_URL, SUPABASE_ANON_KEY)

# ---------------- HELPERS ----------------
def load_table(name):
    res = supabase.table(name).select("*").execute()
    return pd.DataFrame(res.data) if res.data else pd.DataFrame()

def euro(x):
    return f"{x:,.2f} €".replace(",", " ").replace(".", ",")

# ---------------- SIDEBAR ----------------
st.sidebar.title("Filtres")

df_dep = load_table("depenses")
annees = sorted(df_dep["annee"].dropna().unique(), reverse=True)
annee = st.sidebar.selectbox("Année", annees)

# ---------------- TABS ----------------
tab_dep, tab_bud, tab_plan = st.tabs(
    ["📋 Dépenses", "📊 Budgets", "📚 Plan comptable"]
)

# ==========================================================
# 📋 DEPENSES
# ==========================================================
with tab_dep:
    st.subheader("Dépenses")

    df_dep_y = df_dep[df_dep["annee"] == annee].copy()
    df_dep_y["montant_ttc"] = pd.to_numeric(df_dep_y["montant_ttc"], errors="coerce").fillna(0)

    display_cols = [
        "depense_id",
        "date",
        "compte",
        "poste",
        "fournisseur",
        "type",
        "sens",
        "montant_ttc",
        "commentaire"
    ]

    st.dataframe(
        df_dep_y[display_cols].sort_values("date"),
        use_container_width=True
    )

    # ---------- AJOUT ----------
    st.markdown("### ➕ Ajouter une dépense")

    with st.form("add_depense"):
        c1, c2, c3 = st.columns(3)

        with c1:
            date = st.date_input("Date")
            compte = st.text_input("Compte")
            poste = st.text_input("Poste")

        with c2:
            fournisseur = st.text_input("Fournisseur")
            type_libre = st.text_input("Type")
            sens = st.selectbox("Sens", ["Charge", "Avoir", "Remboursement"])

        with c3:
            montant = st.number_input("Montant TTC", min_value=0.0, step=0.01)
            commentaire = st.text_input("Commentaire")

        if st.form_submit_button("Enregistrer"):
            supabase.table("depenses").insert({
                "annee": annee,
                "date": str(date),
                "compte": compte,
                "poste": poste,
                "fournisseur": fournisseur,
                "type": type_libre,
                "sens": sens,
                "montant_ttc": montant,
                "commentaire": commentaire
            }).execute()
            st.success("Dépense ajoutée")
            st.rerun()

    # ---------- SUPPRESSION ----------
    st.markdown("### 🗑 Supprimer une dépense")
    dep_id = st.selectbox(
        "Sélectionner une dépense",
        df_dep_y["depense_id"].tolist()
    )

    if st.button("Supprimer la dépense"):
        supabase.table("depenses").delete().eq("depense_id", dep_id).execute()
        st.success("Dépense supprimée")
        st.rerun()

# ==========================================================
# 📊 BUDGETS
# ==========================================================
with tab_bud:
    st.subheader("Budgets")

    df_bud = load_table("budgets")
    df_bud_y = df_bud[df_bud["annee"] == annee].copy()

    st.dataframe(
        df_bud_y[["id", "groupe_compte", "libelle_groupe", "budget"]]
        .sort_values("groupe_compte"),
        use_container_width=True
    )

    # ---------- AJOUT / MODIF ----------
    st.markdown("### ➕ Ajouter / modifier un budget")

    with st.form("add_budget"):
        g = st.text_input("Groupe de compte (ex: 601)")
        lg = st.text_input("Libellé groupe")
        b = st.number_input("Budget", min_value=0.0, step=100.0)

        if st.form_submit_button("Enregistrer"):
            supabase.table("budgets").insert({
                "annee": annee,
                "groupe_compte": g,
                "libelle_groupe": lg,
                "budget": b
            }).execute()
            st.success("Budget enregistré")
            st.rerun()

    # ---------- SUPPRESSION ----------
    st.markdown("### 🗑 Supprimer un budget")
    bud_id = st.selectbox(
        "Sélectionner un budget",
        df_bud_y["id"].tolist()
    )

    if st.button("Supprimer le budget"):
        supabase.table("budgets").delete().eq("id", bud_id).execute()
        st.success("Budget supprimé")
        st.rerun()

# ==========================================================
# 📚 PLAN COMPTABLE
# ==========================================================
with tab_plan:
    st.subheader("Plan comptable")

    df_plan = load_table("plan_comptable")

    # nettoyage visuel
    df_plan = df_plan[
        (df_plan["compte_8"].notna()) &
        (df_plan["compte_8"] != "") &
        (df_plan["libelle_groupe"] != "000")
    ]

    st.dataframe(
        df_plan.sort_values(["groupe_compte", "compte_8"]),
        use_container_width=True
    )

   
