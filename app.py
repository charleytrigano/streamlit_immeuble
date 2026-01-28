import streamlit as st
import pandas as pd
from supabase import create_client

# ======================
# CONFIG
# ======================
st.set_page_config(page_title="Pilotage des charges", layout="wide")

SUPABASE_URL = st.secrets["SUPABASE_URL"]
SUPABASE_KEY = st.secrets["SUPABASE_ANON_KEY"]

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# ======================
# LOADERS
# ======================
@st.cache_data
def load_table(name):
    data = supabase.table(name).select("*").execute().data
    return pd.DataFrame(data)

df_dep = load_table("depenses")
df_plan = load_table("plan_comptable")
df_bud = load_table("budgets")

# ======================
# FILTRE ANNÉE
# ======================
annee = st.sidebar.selectbox(
    "Année",
    sorted(df_dep["annee"].unique())
)

# ======================
# KPI
# ======================
dep_y = df_dep[df_dep["annee"] == annee]
bud_y = df_bud[df_bud["annee"] == annee]

total_dep = dep_y["montant_ttc"].sum()
total_bud = bud_y["budget"].sum()
ecart = total_bud - total_dep

c1, c2, c3 = st.columns(3)
c1.metric("Dépenses réelles", f"{total_dep:,.0f} €")
c2.metric("Budget", f"{total_bud:,.0f} €")
c3.metric("Écart", f"{ecart:,.0f} €")

st.divider()

# ======================
# ONGLET PRINCIPAL
# ======================
tabs = st.tabs(["📊 Dépenses", "📘 Plan comptable", "💰 Budget"])

# ======================
# DÉPENSES (LECTURE SEULE)
# ======================
with tabs[0]:
    st.subheader("État des dépenses")

    df_disp = dep_y.merge(
        df_plan[["compte_8", "groupe_compte", "libelle_groupe"]],
        left_on="compte",
        right_on="compte_8",
        how="left"
    )

    st.dataframe(
        df_disp[
            [
                "date",
                "annee",
                "compte",
                "poste",
                "fournisseur",
                "groupe_compte",
                "libelle_groupe",
                "montant_ttc",
                "commentaire",
            ]
        ],
        use_container_width=True
    )


st.subheader("➕ Ajouter une dépense")

with st.form("add_depense"):
    d1, d2, d3 = st.columns(3)

    date = d1.date_input("Date")
    compte = d2.selectbox("Compte", df_plan["compte_8"].sort_values())
    fournisseur = d3.text_input("Fournisseur")

    poste = st.text_input("Libellé / Poste")
    montant = st.number_input("Montant TTC", min_value=0.0)
    commentaire = st.text_area("Commentaire")

    submit = st.form_submit_button("Enregistrer")

    if submit:
        supabase.table("depenses").insert({
            "annee": annee,
            "date": str(date),
            "compte": compte,
            "poste": poste,
            "fournisseur": fournisseur,
            "montant_ttc": montant,
            "commentaire": commentaire
        }).execute()

        st.success("Dépense ajoutée")
        st.experimental_rerun()

# ======================
# PLAN COMPTABLE (VERROUILLÉ)
# ======================
with tabs[1]:
    st.subheader("Plan comptable (lecture seule)")

    df_pc = df_plan[
        (df_plan["compte_8"].notna()) &
        (df_plan["libelle_groupe"] != "000")
    ]

    st.dataframe(
        df_pc.sort_values(["groupe_compte", "compte_8"]),
        use_container_width=True
    )

    st.info("Le plan comptable est verrouillé.")

# ======================
# BUDGET (MODIFIABLE)
# ======================
with tabs[2]:
    st.subheader("Budget par groupe")

    st.dataframe(
        bud_y[
            [
                "groupe_compte",
                "libelle_groupe",
                "budget"
            ]
        ].sort_values("groupe_compte"),
        use_container_width=True
    )

    st.divider()
    st.subheader("Ajouter / modifier un budget")

    col1, col2, col3 = st.columns(3)

    with col1:
        grp = st.selectbox(
            "Groupe",
            sorted(df_plan["groupe_compte"].unique())
        )

    with col2:
        lib_grp = (
            df_plan[df_plan["groupe_compte"] == grp]
            ["libelle_groupe"]
            .iloc[0]
        )
        st.text_input("Libellé groupe", lib_grp, disabled=True)

    with col3:
        montant = st.number_input("Budget", min_value=0.0)

    if st.button("💾 Enregistrer"):
        supabase.table("budgets").upsert(
            {
                "annee": annee,
                "groupe_compte": grp,
                "libelle_groupe": lib_grp,
                "budget": montant,
            }
        ).execute()
        st.success("Budget enregistré")
        st.experimental_rerun()