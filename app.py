import streamlit as st
import pandas as pd
from supabase import create_client

# =====================================================
# CONFIG
# =====================================================
st.set_page_config(page_title="📄 État des dépenses", layout="wide")

# =====================================================
# SUPABASE
# =====================================================
@st.cache_resource
def get_supabase():
    return create_client(
        st.secrets["SUPABASE_URL"],
        st.secrets["SUPABASE_ANON_KEY"]
    )

# =====================================================
# UTILS
# =====================================================
def euro(x):
    return f"{x:,.2f} €".replace(",", " ").replace(".", ",")

# =====================================================
# MAIN
# =====================================================
def main():
    supabase = get_supabase()

    st.title("📄 État des dépenses")

    # =================================================
    # CHARGEMENT DÉPENSES
    # =================================================
    resp = (
        supabase
        .table("depenses")
        .select("""
            depense_id,
            annee,
            compte,
            poste,
            fournisseur,
            date,
            montant_ttc,
            type,
            commentaire,
            lot_id,
            pdf_url
        """)
        .order("date", desc=True)
        .execute()
    )

    df = pd.DataFrame(resp.data)

    if df.empty:
        st.warning("Aucune dépense enregistrée.")
        return

    # Typage
    df["annee"] = df["annee"].astype(int)
    df["montant_ttc"] = df["montant_ttc"].astype(float)
    df["date"] = pd.to_datetime(df["date"])

    # =================================================
    # SIDEBAR – FILTRES
    # =================================================
    st.sidebar.header("🔎 Filtres")

    annee = st.sidebar.selectbox(
        "Année",
        sorted(df["annee"].unique())
    )

    compte = st.sidebar.selectbox(
        "Compte",
        ["Tous"] + sorted(df["compte"].dropna().unique().tolist())
    )

    fournisseur = st.sidebar.selectbox(
        "Fournisseur",
        ["Tous"] + sorted(df["fournisseur"].dropna().unique().tolist())
    )

    poste = st.sidebar.selectbox(
        "Poste",
        ["Tous"] + sorted(df["poste"].dropna().unique().tolist())
    )

    lot = st.sidebar.selectbox(
        "Lot",
        ["Tous"] + sorted(df["lot_id"].dropna().astype(str).unique().tolist())
    )

    # Application filtres
    df_f = df[df["annee"] == annee]

    if compte != "Tous":
        df_f = df_f[df_f["compte"] == compte]

    if fournisseur != "Tous":
        df_f = df_f[df_f["fournisseur"] == fournisseur]

    if poste != "Tous":
        df_f = df_f[df_f["poste"] == poste]

    if lot != "Tous":
        df_f = df_f[df_f["lot_id"].astype(str) == lot]

    # =================================================
    # KPI
    # =================================================
    col1, col2, col3 = st.columns(3)

    col1.metric("💸 Total dépenses", euro(df_f["montant_ttc"].sum()))
    col2.metric("🧾 Nombre de lignes", len(df_f))
    col3.metric(
        "📊 Dépense moyenne",
        euro(df_f["montant_ttc"].mean()) if len(df_f) > 0 else "0 €"
    )

    # =================================================
    # TABLEAU
    # =================================================
    df_f["Facture"] = df_f["pdf_url"].apply(
        lambda x: f"[📄 Ouvrir]({x})" if pd.notna(x) and x != "" else ""
    )

    st.dataframe(
        df_f[[
            "date",
            "compte",
            "poste",
            "fournisseur",
            "montant_ttc",
            "type",
            "lot_id",
            "commentaire",
            "Facture"
        ]].rename(columns={
            "date": "Date",
            "compte": "Compte",
            "poste": "Poste",
            "fournisseur": "Fournisseur",
            "montant_ttc": "Montant TTC (€)",
            "type": "Type",
            "lot_id": "Lot",
            "commentaire": "Commentaire"
        }),
        use_container_width=True
    )

    # =================================================
    # CRUD
    # =================================================
    st.divider()
    tab_add, tab_edit, tab_del = st.tabs(["➕ Ajouter", "✏️ Modifier", "🗑 Supprimer"])

    # -----------------------------
    # AJOUT
    # -----------------------------
    with tab_add:
        st.subheader("Ajouter une dépense")

        with st.form("add_depense"):
            data = {
                "annee": st.number_input("Année", min_value=2000, max_value=2100, value=annee),
                "date": st.date_input("Date"),
                "compte": st.text_input("Compte (8 chiffres)"),
                "poste": st.text_input("Poste"),
                "fournisseur": st.text_input("Fournisseur"),
                "montant_ttc": st.number_input("Montant TTC", step=0.01),
                "type": st.selectbox("Type", ["Charge", "Avoir", "Remboursement"]),
                "lot_id": st.text_input("Lot (optionnel)"),
                "commentaire": st.text_area("Commentaire"),
                "pdf_url": st.text_input("Lien facture (pdf_url)")
            }

            if st.form_submit_button("Enregistrer"):
                supabase.table("depenses").insert(data).execute()
                st.success("Dépense ajoutée")
                st.experimental_rerun()

    # -----------------------------
    # MODIFIER
    # -----------------------------
    with tab_edit:
        st.subheader("Modifier une dépense")

        dep_id = st.selectbox(
            "Sélection",
            df_f["depense_id"],
            format_func=lambda x: f"ID {x}"
        )

        dep = df[df["depense_id"] == dep_id].iloc[0]

        with st.form("edit_depense"):
            new_data = {
                "date": st.date_input("Date", dep["date"]),
                "compte": st.text_input("Compte", dep["compte"]),
                "poste": st.text_input("Poste", dep["poste"]),
                "fournisseur": st.text_input("Fournisseur", dep["fournisseur"]),
                "montant_ttc": st.number_input("Montant TTC", value=float(dep["montant_ttc"]), step=0.01),
                "type": st.selectbox("Type", ["Charge", "Avoir", "Remboursement"],
                                     index=["Charge", "Avoir", "Remboursement"].index(dep["type"])),
                "lot_id": st.text_input("Lot", dep["lot_id"] if dep["lot_id"] else ""),
                "commentaire": st.text_area("Commentaire", dep["commentaire"]),
                "pdf_url": st.text_input("Lien facture", dep["pdf_url"])
            }

            if st.form_submit_button("Mettre à jour"):
                supabase.table("depenses").update(new_data).eq("depense_id", dep_id).execute()
                st.success("Dépense modifiée")
                st.experimental_rerun()

    # -----------------------------
    # SUPPRIMER
    # -----------------------------
    with tab_del:
        st.subheader("Supprimer une dépense")

        del_id = st.selectbox(
            "Sélection",
            df_f["depense_id"],
            format_func=lambda x: f"ID {x}"
        )

        if st.button("❌ Supprimer définitivement"):
            supabase.table("depenses").delete().eq("depense_id", del_id).execute()
            st.success("Dépense supprimée")
            st.experimental_rerun()


# =====================================================
# RUN
# =====================================================
if __name__ == "__main__":
    main()