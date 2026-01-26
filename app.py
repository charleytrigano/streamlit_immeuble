import streamlit as st
import pandas as pd
from supabase import create_client

# =====================================================
# CONFIG
# =====================================================
st.set_page_config(page_title="Pilotage des charges", layout="wide")

# =====================================================
# SUPABASE
# =====================================================
@st.cache_resource
def get_supabase():
    return create_client(
        st.secrets["SUPABASE_URL"],
        st.secrets["SUPABASE_ANON_KEY"]
    )

supabase = get_supabase()

# =====================================================
# UTILS
# =====================================================
def euro(x):
    return f"{x:,.2f} €".replace(",", " ").replace(".", ",")

# =====================================================
# SIDEBAR
# =====================================================
st.sidebar.title("Navigation")

page = st.sidebar.radio(
    "Aller à",
    ["📄 État des dépenses"]
)

annee = st.sidebar.selectbox(
    "Année",
    [2023, 2024, 2025, 2026],
    index=2
)

# =====================================================
# LOAD DEPENSES
# =====================================================
def load_depenses():
    resp = (
        supabase
        .table("depenses")
        .select("*")
        .eq("annee", annee)
        .order("id")
        .execute()
    )
    return pd.DataFrame(resp.data)

# =====================================================
# 📄 ÉTAT DES DÉPENSES
# =====================================================
st.title("📄 État des dépenses")

df = load_depenses()

# -------------------------
# KPI
# -------------------------
if not df.empty:
    c1, c2 = st.columns(2)
    c1.metric("Total dépenses", euro(df["montant_ttc"].sum()))
    c2.metric("Nombre de lignes", len(df))

    # -------------------------
    # TABLEAU
    # -------------------------
    st.dataframe(
        df[[
            "id",
            "compte",
            "fournisseur",
            "commentaire",
            "montant_ttc",
            "lien_facture"
        ]],
        use_container_width=True
    )
else:
    st.info("Aucune dépense pour cette année.")

# =====================================================
# ➕ AJOUTER UNE DÉPENSE
# =====================================================
st.markdown("### ➕ Ajouter une dépense")

with st.form("add_depense", clear_on_submit=True):
    compte = st.text_input("Compte")
    fournisseur = st.text_input("Fournisseur")
    commentaire = st.text_area("Commentaire")
    montant = st.number_input("Montant TTC", value=0.0, step=0.01)
    lien_facture = st.text_input("Lien facture (Supabase Storage)")

    submitted = st.form_submit_button("Ajouter")

    if submitted:
        supabase.table("depenses").insert({
            "annee": annee,
            "compte": compte,
            "fournisseur": fournisseur,
            "commentaire": commentaire,
            "montant_ttc": montant,
            "lien_facture": lien_facture
        }).execute()

        st.success("Dépense ajoutée")
        st.experimental_rerun()

# =====================================================
# ✏️ MODIFIER UNE DÉPENSE
# =====================================================
st.markdown("### ✏️ Modifier une dépense")

if not df.empty:
    dep_id = st.selectbox(
        "Sélectionner une dépense",
        df["id"],
        format_func=lambda i: (
            f"{df.loc[df.id == i, 'compte'].values[0]} | "
            f"{df.loc[df.id == i, 'fournisseur'].values[0]} | "
            f"{euro(df.loc[df.id == i, 'montant_ttc'].values[0])}"
        )
    )

    dep = df[df.id == dep_id].iloc[0]

    with st.form("edit_depense"):
        compte_e = st.text_input("Compte", dep["compte"])
        fournisseur_e = st.text_input("Fournisseur", dep["fournisseur"])
        commentaire_e = st.text_area("Commentaire", dep["commentaire"])
        montant_e = st.number_input(
            "Montant TTC",
            value=float(dep["montant_ttc"]),
            step=0.01
        )
        lien_facture_e = st.text_input(
            "Lien facture",
            dep["lien_facture"]
        )

        submitted = st.form_submit_button("Modifier")

        if submitted:
            supabase.table("depenses").update({
                "compte": compte_e,
                "fournisseur": fournisseur_e,
                "commentaire": commentaire_e,
                "montant_ttc": montant_e,
                "lien_facture": lien_facture_e
            }).eq("id", dep_id).execute()

            st.success("Dépense modifiée")
            st.experimental_rerun()

# =====================================================
# 🗑 SUPPRIMER UNE DÉPENSE
# =====================================================
st.markdown("### 🗑 Supprimer une dépense")

if not df.empty:
    del_id = st.selectbox(
        "Choisir la dépense à supprimer",
        df["id"],
        key="delete",
        format_func=lambda i: (
            f"{df.loc[df.id == i, 'compte'].values[0]} | "
            f"{df.loc[df.id == i, 'fournisseur'].values[0]} | "
            f"{euro(df.loc[df.id == i, 'montant_ttc'].values[0])}"
        )
    )

    if st.button("Supprimer définitivement"):
        supabase.table("depenses").delete().eq("id", del_id).execute()
        st.success("Dépense supprimée")
        st.experimental_rerun()