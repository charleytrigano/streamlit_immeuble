import streamlit as st
import pandas as pd
import uuid
from supabase import create_client

# =========================
# CONFIG
# =========================
st.set_page_config(
    page_title="Pilotage des charges",
    layout="wide"
)

SUPABASE_URL = st.secrets["SUPABASE_URL"]
SUPABASE_KEY = st.secrets["SUPABASE_ANON_KEY"]
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

BUCKET_FACTURES = "factures"

# =========================
# HELPERS
# =========================
def euro(v):
    return f"{v:,.2f} €".replace(",", " ").replace(".", ",")

def load_table(name, filters=None):
    q = supabase.table(name).select("*")
    if filters:
        for k, v in filters.items():
            q = q.eq(k, v)
    return pd.DataFrame(q.execute().data)

def load_view(name):
    return pd.DataFrame(
        supabase.table(name).select("*").execute().data
    )

def upload_facture(file):
    path = f"{uuid.uuid4()}_{file.name}"
    supabase.storage.from_(BUCKET_FACTURES).upload(
        path, file.getvalue(), {"content-type": file.type}
    )
    return path

def facture_url(path):
    if not path:
        return None
    return supabase.storage.from_(BUCKET_FACTURES).get_public_url(path)

# =========================
# SIDEBAR
# =========================
page = st.sidebar.radio(
    "Navigation",
    [
        "📄 État des dépenses",
        "🚨 Contrôle de répartition",
        "💰 Budget",
        "📊 Budget vs Réel",
        "📈 Statistiques",
    ],
)

annee = st.sidebar.selectbox(
    "Année",
    [2023, 2024, 2025, 2026],
    index=2,
)

# =========================
# 📄 ÉTAT DES DÉPENSES
# =========================
if page == "📄 État des dépenses":
    st.title("📄 État des dépenses")

    df = load_table("depenses", {"annee": annee})

    if not df.empty:
        df["facture"] = df["facture_path"].apply(facture_url)

        st.dataframe(
            df[
                [
                    "date",
                    "poste",
                    "groupe_compte",
                    "compte",
                    "fournisseur",
                    "montant_ttc",
                    "commentaire",
                    "facture",
                ]
            ],
            use_container_width=True,
        )

    st.divider()
    st.subheader("➕ Ajouter / Modifier une dépense")

    with st.form("depense_form"):
        dep_id = st.text_input("ID (laisser vide pour création)")
        date = st.date_input("Date")
        poste = st.text_input("Poste")
        groupe = st.text_input("Groupe de compte")
        compte = st.text_input("Compte")
        fournisseur = st.text_input("Fournisseur")
        montant = st.number_input("Montant TTC", min_value=0.0, step=0.01)
        commentaire = st.text_area("Commentaire")
        facture = st.file_uploader("Facture (PDF / image)", type=["pdf", "jpg", "png"])

        submit = st.form_submit_button("Enregistrer")

    if submit:
        facture_path = upload_facture(facture) if facture else None

        payload = {
            "date": str(date),
            "annee": annee,
            "poste": poste,
            "groupe_compte": groupe,
            "compte": compte,
            "fournisseur": fournisseur,
            "montant_ttc": montant,
            "commentaire": commentaire,
        }

        if facture_path:
            payload["facture_path"] = facture_path

        if dep_id:
            supabase.table("depenses").update(payload).eq("id", dep_id).execute()
            st.success("Dépense mise à jour")
        else:
            supabase.table("depenses").insert(payload).execute()
            st.success("Dépense créée")

        st.rerun()

# =========================
# 🚨 CONTRÔLE RÉPARTITION
# =========================
elif page == "🚨 Contrôle de répartition":
    st.title("🚨 Contrôle de répartition")

    df = load_view("v_controle_repartition")

    if df.empty:
        st.success("Toutes les dépenses sont correctement réparties 🎉")
    else:
        st.error("Certaines dépenses ne sont PAS réparties à 100 %")
        st.dataframe(df, use_container_width=True)

# =========================
# 💰 BUDGET
# =========================
elif page == "💰 Budget":
    st.title("💰 Budget")

    df = load_table("budgets", {"annee": annee})

    if df.empty:
        st.warning("Aucun budget pour cette année")
    else:
        st.metric("Budget total", euro(df["budget"].sum()))
        st.dataframe(
            df[["groupe_compte", "compte", "budget"]],
            use_container_width=True,
        )

# =========================
# 📊 BUDGET VS RÉEL
# =========================
elif page == "📊 Budget vs Réel":
    st.title("📊 Budget vs Réel")

    df = load_view("v_budget_vs_reel")

    if df.empty:
        st.warning("Aucune donnée")
    else:
        charges_reelles = df["charges_reelles"].sum()
        charges_reparties = df["charges_reparties"].sum()
        budget = df["budget"].sum()

        c1, c2, c3 = st.columns(3)
        c1.metric("Budget", euro(budget))
        c2.metric("Charges réelles", euro(charges_reelles))
        c3.metric("Écart", euro(budget - charges_reelles))

        st.dataframe(df, use_container_width=True)

# =========================
# 📈 STATISTIQUES
# =========================
elif page == "📈 Statistiques":
    st.title("📈 Statistiques")

    df = load_table("depenses", {"annee": annee})

    if df.empty:
        st.warning("Aucune dépense")
    else:
        st.metric("Nombre de dépenses", len(df))
        st.metric("Montant total facturé", euro(df["montant_ttc"].sum()))