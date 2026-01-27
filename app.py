import io
import uuid
from datetime import date

import pandas as pd
import streamlit as st
from supabase import create_client


# =========================
# CONFIG
# =========================
st.set_page_config(page_title="Pilotage des charges - Dépenses", layout="wide")


# =========================
# SUPABASE
# =========================
@st.cache_resource
def get_supabase():
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_ANON_KEY"]
    return create_client(url, key)


supabase = get_supabase()


# =========================
# HELPERS
# =========================
def euro(x: float | int | None) -> str:
    if x is None:
        x = 0
    return f"{x:,.2f} €".replace(",", " ").replace(".", ",")


def get_facture_public_url(path: str | None) -> str | None:
    """Retourne l'URL publique de la facture (ou None)."""
    if not path:
        return None
    try:
        return supabase.storage.from_("factures").get_public_url(path)
    except Exception:
        return None


def upload_facture(annee: int, depense_id: str, uploaded_file) -> str | None:
    """
    Envoie la facture dans le bucket 'factures' et renvoie le chemin (facture_path)
    stocké dans la table depenses.
    """
    if uploaded_file is None:
        return None

    ext = uploaded_file.name.split(".")[-1].lower()
    # chemin logique dans le bucket : 2025/<depense_id>_<uuid>.ext
    file_path = f"{annee}/{depense_id}_{uuid.uuid4().hex}.{ext}"

    file_bytes = uploaded_file.getvalue()
    file_obj = io.BytesIO(file_bytes)

    try:
        supabase.storage.from_("factures").upload(
            file_path,
            file_obj,
            {"cache-control": "3600", "upsert": "true"},
        )
        return file_path
    except Exception as e:
        st.error(f"Erreur lors de l'upload de la facture : {e}")
        return None


# =========================
# FILTRES
# =========================
st.sidebar.title("Filtres")

annee = st.sidebar.selectbox("Année", [2023, 2024, 2025, 2026], index=2)

st.title("🏢 Pilotage des charges de l’immeuble")
st.markdown("## 📄 État des dépenses")


# =========================
# CHARGEMENT DES DÉPENSES
# =========================
try:
    res = (
        supabase.table("depenses")
        .select("*")
        .eq("annee", annee)
        .order("date")
        .execute()
    )
    depenses_data = res.data or []
except Exception as e:
    st.error(f"Erreur Supabase lors du chargement des dépenses : {e}")
    depenses_data = []

df = pd.DataFrame(depenses_data)

# On s'assure que certaines colonnes existent au moins vides
for col in ["date", "compte", "fournisseur", "montant_ttc", "commentaire", "facture_path"]:
    if col not in df.columns:
        df[col] = None

# Colonnes types
df["montant_ttc"] = pd.to_numeric(df["montant_ttc"], errors="coerce").fillna(0.0)

# Colonne lien facture (Markdown cliquable)
df["facture"] = df["facture_path"].apply(
    lambda p: f"[📄 Voir]({get_facture_public_url(p)})" if p else ""
)


# =========================
# KPI FIABLES
# =========================
st.markdown("### 🔎 Synthèse des charges réelles")

if df.empty:
    st.info(f"Aucune dépense pour l'année {annee}.")
    total = 0.0
    n = 0
    moy = 0.0
    mt_avec = 0.0
    mt_sans = 0.0
else:
    total = df["montant_ttc"].sum()
    n = len(df)
    moy = total / n if n > 0 else 0.0
    mask_avec = df["facture_path"].notna() & (df["facture_path"] != "")
    mt_avec = df.loc[mask_avec, "montant_ttc"].sum()
    mt_sans = df.loc[~mask_avec, "montant_ttc"].sum()

col1, col2, col3, col4 = st.columns(4)

col1.metric("Total charges réelles", euro(total))
col2.metric("Nombre de lignes", f"{n}")
col3.metric("Charge moyenne / ligne", euro(moy))
col4.metric("Montant sans facture", euro(mt_sans))

st.caption(
    f"Montant avec facture : **{euro(mt_avec)}** / Montant sans facture : **{euro(mt_sans)}**"
)

st.markdown("---")


# =========================
# TABLEAU DES DÉPENSES
# =========================
st.markdown("### 📋 Détails des dépenses")

if df.empty:
    st.info(f"Aucune dépense pour l'année {annee}.")
else:
    colonnes_affichage = [
        "date",
        "compte",
        "fournisseur",
        "montant_ttc",
        "commentaire",
        "facture",
    ]

    st.dataframe(
        df[colonnes_affichage].rename(
            columns={
                "date": "Date",
                "compte": "Compte",
                "fournisseur": "Fournisseur",
                "montant_ttc": "Montant TTC",
                "commentaire": "Commentaire",
                "facture": "Facture",
            }
        ),
        use_container_width=True,
    )

st.markdown("---")


# =========================
# FORMULAIRE – AJOUTER
# =========================
st.subheader("➕ Ajouter une dépense")

with st.form("form_ajout"):
    col_a, col_b, col_c = st.columns(3)
    col_d, col_e = st.columns(2)

    date_dep = col_a.date_input("Date", value=date.today())
    compte_dep = col_b.text_input("Compte")
    fournisseur_dep = col_c.text_input("Fournisseur")
    montant_dep = col_d.number_input("Montant TTC", min_value=0.0, step=0.01)
    commentaire_dep = col_e.text_input("Commentaire", value="", placeholder="Optionnel")
    fichier_dep = st.file_uploader("Facture (PDF, JPG, PNG…)", type=None)

    submitted_ajout = st.form_submit_button("Enregistrer la dépense")

if submitted_ajout:
    try:
        # 1) créer la dépense pour obtenir son id
        insert_res = (
            supabase.table("depenses")
            .insert(
                {
                    "annee": annee,
                    "date": str(date_dep),
                    "compte": compte_dep,
                    "fournisseur": fournisseur_dep,
                    "montant_ttc": float(montant_dep),
                    "commentaire": commentaire_dep,
                    # on mettra facture_path à jour après upload
                }
            )
            .execute()
        )
        new_rows = insert_res.data or []
        if not new_rows:
            st.error("Insertion échouée (aucune ligne retournée).")
        else:
            new_dep = new_rows[0]
            dep_id = new_dep["id"]

            facture_path = upload_facture(annee, dep_id, fichier_dep)
            if facture_path:
                supabase.table("depenses").update(
                    {"facture_path": facture_path}
                ).eq("id", dep_id).execute()

            st.success("Dépense ajoutée avec succès.")
            st.experimental_rerun()
    except Exception as e:
        st.error(f"Erreur Supabase lors de l'ajout : {e}")


st.markdown("---")


# =========================
# FORMULAIRE – MODIFIER
# =========================
st.subheader("✏️ Modifier une dépense")

if df.empty:
    st.info("Aucune dépense à modifier.")
else:
    # Liste lisible pour la sélection
    df["label"] = df.apply(
        lambda r: f"{r.get('date', '')} | {r.get('compte', '')} | "
        f"{euro(r.get('montant_ttc', 0))} | {r.get('fournisseur', '')}",
        axis=1,
    )

    row_map = {row["label"]: row for _, row in df.iterrows()}
    choix = st.selectbox("Sélectionner une dépense", list(row_map.keys()))
    row_sel = row_map[choix]
    dep_id_edit = row_sel["id"]

    with st.form("form_edit"):
        col1, col2, col3 = st.columns(3)
        col4, col5 = st.columns(2)

        date_edit = col1.date_input(
            "Date", value=pd.to_datetime(row_sel["date"]).date()
        )
        compte_edit = col2.text_input("Compte", value=row_sel["compte"] or "")
        fournisseur_edit = col3.text_input(
            "Fournisseur", value=row_sel["fournisseur"] or ""
        )
        montant_edit = col4.number_input(
            "Montant TTC",
            min_value=0.0,
            step=0.01,
            value=float(row_sel["montant_ttc"] or 0.0),
        )
        commentaire_edit = col5.text_input(
            "Commentaire", value=row_sel["commentaire"] or ""
        )
        fichier_edit = st.file_uploader(
            "Remplacer la facture (laisser vide pour garder l'existante)",
            type=None,
            key="edit_upload",
        )

        submitted_edit = st.form_submit_button("Mettre à jour")

    if submitted_edit:
        try:
            update_data = {
                "date": str(date_edit),
                "compte": compte_edit,
                "fournisseur": fournisseur_edit,
                "montant_ttc": float(montant_edit),
                "commentaire": commentaire_edit,
            }

            # Upload éventuel d'une nouvelle facture
            if fichier_edit is not None:
                new_path = upload_facture(annee, dep_id_edit, fichier_edit)
                if new_path:
                    update_data["facture_path"] = new_path

            supabase.table("depenses").update(update_data).eq("id", dep_id_edit).execute()
            st.success("Dépense mise à jour avec succès.")
            st.experimental_rerun()
        except Exception as e:
            st.error(f"Erreur Supabase lors de la mise à jour : {e}")


st.markdown("---")


# =========================
# SUPPRIMER
# =========================
st.subheader("🗑️ Supprimer une dépense")

if df.empty:
    st.info("Aucune dépense à supprimer.")
else:
    df["label_delete"] = df.apply(
        lambda r: f"{r.get('date', '')} | {r.get('compte', '')} | "
        f"{euro(r.get('montant_ttc', 0))} | {r.get('fournisseur', '')}",
        axis=1,
    )
    map_delete = {row["label_delete"]: row for _, row in df.iterrows()}
    choix_del = st.selectbox("Sélectionner une dépense à supprimer", list(map_delete.keys()))
    row_del = map_delete[choix_del]
    dep_id_del = row_del["id"]

    if st.button("Confirmer la suppression", type="primary"):
        try:
            supabase.table("depenses").delete().eq("id", dep_id_del).execute()
            st.success("Dépense supprimée.")
            st.experimental_rerun()
        except Exception as e:
            st.error(f"Erreur Supabase lors de la suppression : {e}")