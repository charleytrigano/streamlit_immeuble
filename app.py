import streamlit as st
import pandas as pd
from supabase import create_client

# ---------------- CONFIG ----------------
st.set_page_config(page_title="Pilotage des charges", layout="wide")

SUPABASE_URL = st.secrets["SUPABASE_URL"]
SUPABASE_KEY = st.secrets["SUPABASE_ANON_KEY"]
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# ---------------- UTILS ----------------
@st.cache_data
def load_table(name):
    return pd.DataFrame(
        supabase.table(name).select("*").execute().data
    )

def refresh():
    st.cache_data.clear()
    st.experimental_rerun()

# ---------------- DATA ----------------
df_dep = load_table("depenses")
df_bud = load_table("budgets")
df_plan = load_table("plan_comptable")

# ---------------- SIDEBAR ----------------
annees = sorted(df_dep["annee"].dropna().unique())
annee = st.sidebar.selectbox("Année", annees)

# ---------------- KPI ----------------
dep_y = df_dep[df_dep["annee"] == annee]
bud_y = df_bud[df_bud["annee"] == annee]

total_dep = dep_y["montant"].sum()
total_bud = bud_y["budget"].sum()
ecart = total_bud - total_dep

c1, c2, c3 = st.columns(3)
c1.metric("Dépenses", f"{total_dep:,.2f} €")
c2.metric("Budget", f"{total_bud:,.2f} €")
c3.metric("Écart", f"{ecart:,.2f} €")

# ---------------- ONGLET ----------------
tab1, tab2 = st.tabs(["Dépenses", "Budgets"])

# ======================================================
# ===================== DEPENSES =======================
# ======================================================
with tab1:
    st.subheader("Dépenses")

    st.dataframe(
        dep_y.sort_values("date"),
        use_container_width=True
    )

    with st.expander("➕ Ajouter une dépense"):
        with st.form("add_dep"):
            date = st.date_input("Date")
            compte = st.selectbox("Compte", df_plan["compte_8"])
            ligne = df_plan[df_plan["compte_8"] == compte].iloc[0]

            montant = st.number_input("Montant", step=0.01)
            fournisseur = st.text_input("Fournisseur")
            commentaire = st.text_input("Commentaire")

            if st.form_submit_button("Ajouter"):
                supabase.table("depenses").insert({
                    "date": str(date),
                    "annee": date.year,
                    "compte_8": compte,
                    "libelle": ligne["libelle"],
                    "groupe_compte": ligne["groupe_compte"],
                    "libelle_groupe": ligne["libelle_groupe"],
                    "montant": montant,
                    "fournisseur": fournisseur,
                    "commentaire": commentaire
                }).execute()
                refresh()

    with st.expander("🗑 Supprimer une dépense"):
        dep_id = st.selectbox(
            "Dépense",
            dep_y["depense_id"],
            format_func=lambda x: f"ID {x}"
        )
        if st.button("Supprimer"):
            supabase.table("depenses").delete().eq(
                "depense_id", dep_id
            ).execute()
            refresh()

# ======================================================
# ====================== BUDGETS =======================
# ======================================================
with tab2:
    st.subheader("Budgets par groupe")

    grp = (
        bud_y.groupby(["groupe_compte", "libelle_groupe"], as_index=False)
        .agg({"budget": "sum"})
        .sort_values("groupe_compte")
    )

    st.dataframe(grp, use_container_width=True)

    with st.expander("➕ Ajouter / modifier un budget"):
        with st.form("add_bud"):
            g = st.selectbox(
                "Groupe",
                sorted(df_plan["groupe_compte"].unique())
            )
            lib = df_plan[df_plan["groupe_compte"] == g]["libelle_groupe"].iloc[0]
            val = st.number_input("Budget", step=100.0)

            if st.form_submit_button("Enregistrer"):
                exist = bud_y[bud_y["groupe_compte"] == g]
                if len(exist) == 0:
                    supabase.table("budgets").insert({
                        "annee": annee,
                        "groupe_compte": g,
                        "libelle_groupe": lib,
                        "budget": val
                    }).execute()
                else:
                    supabase.table("budgets").update({
                        "budget": val,
                        "libelle_groupe": lib
                    }).eq("id", exist.iloc[0]["id"]).execute()
                refresh()

    with st.expander("🗑 Supprimer un budget"):
        bid = st.selectbox(
            "Budget",
            bud_y["id"],
            format_func=lambda x: f"ID {x}"
        )
        if st.button("Supprimer"):
            supabase.table("budgets").delete().eq("id", bid).execute()
            refresh()