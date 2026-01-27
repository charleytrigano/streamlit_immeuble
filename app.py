import streamlit as st
import pandas as pd
import uuid
from datetime import date
from supabase import create_client

# =========================
# CONFIG
# =========================
st.set_page_config(page_title="Pilotage des charges", layout="wide")

SUPABASE_URL = st.secrets["SUPABASE_URL"]
SUPABASE_KEY = st.secrets["SUPABASE_ANON_KEY"]

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# =========================
# HELPERS
# =========================
def euro(x):
    return f"{x:,.2f} €".replace(",", " ").replace(".", ",")

def load_depenses():
    res = supabase.table("depenses").select("*").order("date", desc=True).execute()
    return pd.DataFrame(res.data)

def upload_facture(depense_id, file):
    ext = file.name.split(".")[-1]
    path = f"{depense_id}.{ext}"

    supabase.storage.from_("factures").upload(
        path,
        file,
        file_options={"content-type": file.type, "upsert": True},
    )
    return path

def facture_url(path):
    if not path:
        return None
    return supabase.storage.from_("factures").get_public_url(path)

# =========================
# UI
# =========================
st.title("🏢 Pilotage des charges de l’immeuble")

tabs = st.tabs([
    "📄 État des dépenses",
    "➕ Ajouter / modifier",
])

# =========================
# ONGLET 1 – ÉTAT DES DÉPENSES
# =========================
with tabs[0]:
    df = load_depenses()

    if df.empty:
        st.info("Aucune dépense enregistrée.")
    else:
        df["facture"] = df["facture_path"].apply(
            lambda x: f"[📄 Voir]({facture_url(x)})" if x else ""
        )

        st.dataframe(
            df[[
                "date",
                "fournisseur",
                "compte",
                "libelle",
                "montant_ttc",
                "facture",
                "commentaire",
            ]],
            use_container_width=True,
            column_config={
                "montant_ttc": st.column_config.NumberColumn("Montant TTC (€)", format="%.2f"),
                "facture": st.column_config.MarkdownColumn("Facture"),
            }
        )

        st.metric("💰 Total charges réelles", euro(df["montant_ttc"].sum()))

# =========================
# ONGLET 2 – AJOUT / MODIFICATION
# =========================
with tabs[1]:
    df = load_depenses()

    mode = st.radio("Mode", ["Ajouter", "Modifier / Supprimer"], horizontal=True)

    if mode == "Ajouter":
        with st.form("add_depense"):
            fournisseur = st.text_input("Fournisseur")
            compte = st.text_input("Compte")
            libelle = st.text_input("Intitulé")
            montant = st.number_input("Montant TTC", min_value=0.0, step=0.01)
            d = st.date_input("Date", value=date.today())
            commentaire = st.text_area("Commentaire")
            facture = st.file_uploader("Facture (PDF / image)", type=["pdf", "jpg", "png"])

            submit = st.form_submit_button("Enregistrer")

            if submit:
                dep_id = str(uuid.uuid4())

                facture_path = None
                if facture:
                    facture_path = upload_facture(dep_id, facture)

                supabase.table("depenses").insert({
                    "id": dep_id,
                    "date": d.isoformat(),
                    "annee": d.year,
                    "fournisseur": fournisseur,
                    "compte": compte,
                    "libelle": libelle,
                    "montant_ttc": montant,
                    "commentaire": commentaire,
                    "facture_path": facture_path,
                }).execute()

                st.success("Dépense ajoutée avec succès.")
                st.experimental_rerun()

    else:
        if df.empty:
            st.info("Aucune dépense à modifier.")
        else:
            choix = st.selectbox(
                "Sélectionner une dépense",
                df["id"],
                format_func=lambda x: f"{df[df.id == x].iloc[0]['libelle']} – {euro(df[df.id == x].iloc[0]['montant_ttc'])}"
            )

            dep = df[df.id == choix].iloc[0]

            with st.form("edit_depense"):
                fournisseur = st.text_input("Fournisseur", dep["fournisseur"])
                compte = st.text_input("Compte", dep["compte"])
                libelle = st.text_input("Intitulé", dep["libelle"])
                montant = st.number_input("Montant TTC", value=float(dep["montant_ttc"]))
                d = st.date_input("Date", value=pd.to_datetime(dep["date"]))
                commentaire = st.text_area("Commentaire", dep["commentaire"] or "")
                facture = st.file_uploader("Remplacer la facture", type=["pdf", "jpg", "png"])

                col1, col2 = st.columns(2)
                save = col1.form_submit_button("💾 Mettre à jour")
                delete = col2.form_submit_button("🗑️ Supprimer")

                if save:
                    facture_path = dep["facture_path"]
                    if facture:
                        facture_path = upload_facture(dep["id"], facture)

                    supabase.table("depenses").update({
                        "fournisseur": fournisseur,
                        "compte": compte,
                        "libelle": libelle,
                        "montant_ttc": montant,
                        "date": d.isoformat(),
                        "annee": d.year,
                        "commentaire": commentaire,
                        "facture_path": facture_path,
                    }).eq("id", dep["id"]).execute()

                    st.success("Dépense mise à jour.")
                    st.experimental_rerun()

                if delete:
                    supabase.table("depenses").delete().eq("id", dep["id"]).execute()
                    st.success("Dépense supprimée.")
                    st.experimental_rerun()