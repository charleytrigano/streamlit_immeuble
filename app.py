import streamlit as st
import pandas as pd
from supabase import create_client
from datetime import date

# =====================
# CONFIG
# =====================
st.set_page_config(page_title="Pilotage immeuble", layout="wide")

SUPABASE_URL = st.secrets["SUPABASE_URL"]
SUPABASE_KEY = st.secrets["SUPABASE_KEY"]
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# =====================
# UTILS
# =====================
def euro(x):
    if pd.isna(x):
        return "0 €"
    return f"{x:,.2f} €".replace(",", " ").replace(".", ",")

def load_table(name):
    res = supabase.table(name).select("*").execute()
    return pd.DataFrame(res.data)

# =====================
# LOAD DATA
# =====================
df_dep = load_table("depenses")
df_lots = load_table("lots")
df_rep = load_table("repartition_depenses")

# =====================
# NORMALISATION
# =====================
if not df_dep.empty:
    df_dep["date"] = pd.to_datetime(df_dep["date"], errors="coerce")
    df_dep["montant_ttc"] = pd.to_numeric(df_dep["montant_ttc"], errors="coerce").fillna(0)

# =====================
# HEADER KPI
# =====================
st.title("📊 Pilotage des charges")

col1, col2, col3 = st.columns(3)

with col1:
    st.metric("Total dépenses", euro(df_dep["montant_ttc"].sum()))

with col2:
    st.metric("Nombre de dépenses", len(df_dep))

with col3:
    st.metric("Postes distincts", df_dep["poste"].nunique())

st.divider()

# =====================
# TABLEAU DÉPENSES
# =====================
st.subheader("🧾 État des dépenses")

if df_dep.empty:
    st.info("Aucune dépense enregistrée")
else:
    df_display = df_dep.merge(
        df_lots,
        on="lot_id",
        how="left",
        suffixes=("", "_lot")
    )

    df_display["facture"] = df_display["pdf_url"].apply(
        lambda x: f"[Voir]({x})" if pd.notna(x) else ""
    )

    st.dataframe(
        df_display[
            [
                "date",
                "annee",
                "poste",
                "compte",
                "fournisseur",
                "montant_ttc",
                "lot",
                "batiment",
                "tantiemes",
                "facture",
                "commentaire",
            ]
        ],
        use_container_width=True,
        column_config={
            "montant_ttc": st.column_config.NumberColumn("Montant TTC (€)", format="%.2f"),
            "facture": st.column_config.MarkdownColumn("Facture"),
        },
    )

# =====================
# AJOUT DÉPENSE
# =====================
st.divider()
st.subheader("➕ Ajouter une dépense")

with st.form("add_depense"):
    c1, c2, c3 = st.columns(3)

    with c1:
        d_date = st.date_input("Date", value=date.today())
        d_poste = st.text_input("Poste")
        d_compte = st.text_input("Compte")

    with c2:
        d_fournisseur = st.text_input("Fournisseur")
        d_montant = st.number_input("Montant TTC", step=10.0)
        d_lot = st.selectbox("Lot", df_lots["lot_id"])

    with c3:
        d_annee = st.number_input("Année", value=date.today().year)
        d_pdf = st.text_input("URL facture (pdf_url)")
        d_commentaire = st.text_area("Commentaire")

    submitted = st.form_submit_button("Enregistrer")

    if submitted:
        supabase.table("depenses").insert(
            {
                "date": str(d_date),
                "annee": d_annee,
                "poste": d_poste,
                "compte": d_compte,
                "fournisseur": d_fournisseur,
                "montant_ttc": d_montant,
                "lot_id": d_lot,
                "pdf_url": d_pdf if d_pdf else None,
                "commentaire": d_commentaire,
            }
        ).execute()

        st.success("Dépense ajoutée")
        st.rerun()

# =====================
# BUDGET vs RÉEL (PAR POSTE)
# =====================
st.divider()
st.subheader("📉 Réel par poste")

df_poste = (
    df_dep.groupby("poste", dropna=False)["montant_ttc"]
    .sum()
    .reset_index()
    .sort_values("montant_ttc", ascending=False)
)

st.dataframe(
    df_poste,
    use_container_width=True,
    column_config={
        "montant_ttc": st.column_config.NumberColumn("Total TTC (€)", format="%.2f")
    },
)

st.bar_chart(df_poste.set_index("poste"))
