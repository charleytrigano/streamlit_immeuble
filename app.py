import streamlit as st
import pandas as pd
from supabase import create_client

# ===============================
# CONFIG
# ===============================
st.set_page_config(page_title="Pilotage des charges", layout="wide")

SUPABASE_URL = st.secrets["SUPABASE_URL"]
SUPABASE_KEY = st.secrets["SUPABASE_ANON_KEY"]

supabase = create_client(SUPABASE_URL, SUPABASE_ANON_KEY)

COL_DEP_MONTANT = "montant_ttc"

# ===============================
# HELPERS
# ===============================
def load_table(name):
    data = supabase.table(name).select("*").execute().data
    return pd.DataFrame(data)

def insert_row(table, payload):
    supabase.table(table).insert(payload).execute()

def update_row(table, pk, pk_val, payload):
    supabase.table(table).update(payload).eq(pk, pk_val).execute()

def delete_row(table, pk, pk_val):
    supabase.table(table).delete().eq(pk, pk_val).execute()

# ===============================
# LOAD DATA
# ===============================
df_dep = load_table("depenses")
df_bud = load_table("budgets")
df_plan = load_table("plan_comptable")

# Nettoyage plan comptable
df_plan = df_plan[
    (df_plan["libelle_groupe"] != "000") &
    (df_plan["compte_8"].notna()) &
    (df_plan["compte_8"] != "EMPTY")
]

annee = st.sidebar.selectbox("Année", sorted(df_dep["annee"].unique(), reverse=True))

dep_y = df_dep[df_dep["annee"] == annee]
bud_y = df_bud[df_bud["annee"] == annee]

# ===============================
# KPI
# ===============================
total_dep = dep_y[COL_DEP_MONTANT].sum() if not dep_y.empty else 0
total_bud = bud_y["budget"].sum() if not bud_y.empty else 0
ecart = total_bud - total_dep

c1, c2, c3 = st.columns(3)
c1.metric("Total dépenses", f"{total_dep:,.2f} €")
c2.metric("Total budget", f"{total_bud:,.2f} €")
c3.metric("Écart budget", f"{ecart:,.2f} €")

# ===============================
# BUDGET PAR GROUPE
# ===============================
st.subheader("Budget par groupe")

if not bud_y.empty:
    st.dataframe(
        bud_y[["groupe_compte", "libelle_groupe", "budget"]]
        .sort_values("groupe_compte"),
        use_container_width=True
    )
else:
    st.info("Aucun budget pour cette année")

# ===============================
# DÉPENSES
# ===============================
st.subheader("Dépenses")

st.dataframe(
    dep_y[[
        "date",
        "compte_8",
        "groupe_compte",
        "libelle",
        COL_DEP_MONTANT,
        "commentaire"
    ]].sort_values("date"),
    use_container_width=True
)

# ===============================
# CRUD DÉPENSES
# ===============================
st.divider()
st.subheader("Gérer une dépense")

mode = st.radio("Action", ["Ajouter", "Modifier", "Supprimer"], horizontal=True)

if mode == "Ajouter":
    with st.form("add_dep"):
        date = st.date_input("Date")
        compte = st.selectbox("Compte", df_plan["compte_8"])
        ligne = df_plan[df_plan["compte_8"] == compte].iloc[0]
        montant = st.number_input("Montant TTC", step=0.01)
        commentaire = st.text_input("Commentaire")

        if st.form_submit_button("Ajouter"):
            insert_row("depenses", {
                "annee": annee,
                "date": str(date),
                "compte_8": compte,
                "groupe_compte": ligne["groupe_compte"],
                "libelle": ligne["libelle"],
                "montant_ttc": montant,
                "commentaire": commentaire
            })
            st.experimental_rerun()

elif mode == "Modifier":
    dep_id = st.selectbox("Dépense", dep_y["depense_id"])
    row = dep_y[dep_y["depense_id"] == dep_id].iloc[0]

    with st.form("edit_dep"):
        montant = st.number_input("Montant TTC", value=float(row[COL_DEP_MONTANT]))
        commentaire = st.text_input("Commentaire", value=row["commentaire"])

        if st.form_submit_button("Modifier"):
            update_row("depenses", "depense_id", dep_id, {
                "montant_ttc": montant,
                "commentaire": commentaire
            })
            st.experimental_rerun()

else:
    dep_id = st.selectbox("Dépense", dep_y["depense_id"])
    if st.button("Supprimer"):
        delete_row("depenses", "depense_id", dep_id)
        st.experimental_rerun()

# ===============================
# CRUD BUDGETS
# ===============================
st.divider()
st.subheader("Gérer les budgets")

mode_b = st.radio("Action budget", ["Ajouter", "Modifier", "Supprimer"], horizontal=True)

groupes = (
    df_plan[["groupe_compte", "libelle_groupe"]]
    .drop_duplicates()
    .sort_values("groupe_compte")
)

if mode_b == "Ajouter":
    with st.form("add_bud"):
        grp = st.selectbox("Groupe", groupes["groupe_compte"])
        lib = groupes[groupes["groupe_compte"] == grp]["libelle_groupe"].iloc[0]
        montant = st.number_input("Budget", step=0.01)

        if st.form_submit_button("Ajouter"):
            insert_row("budgets", {
                "annee": annee,
                "groupe_compte": grp,
                "libelle_groupe": lib,
                "budget": montant
            })
            st.experimental_rerun()

elif mode_b == "Modifier":
    bud_id = st.selectbox("Budget", bud_y["id"])
    row = bud_y[bud_y["id"] == bud_id].iloc[0]

    with st.form("edit_bud"):
        montant = st.number_input("Budget", value=float(row["budget"]))
        if st.form_submit_button("Modifier"):
            update_row("budgets", "id", bud_id, {"budget": montant})
            st.experimental_rerun()

else:
    bud_id = st.selectbox("Budget", bud_y["id"])
    if st.button("Supprimer"):
        delete_row("budgets", "id", bud_id)
        st.experimental_rerun()
