import streamlit as st
import pandas as pd
from supabase import create_client

# =========================
# CONFIG
# =========================

st.set_page_config(page_title="📊 Pilotage des charges", layout="wide")

SUPABASE_URL = st.secrets["SUPABASE_URL"]
SUPABASE_KEY = st.secrets["SUPABASE_ANON_KEY"]

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

def euro(x):
    if pd.isna(x):
        return "-"
    return f"{x:,.2f} €".replace(",", " ").replace(".", ",")

# =========================
# DATA LOADERS
# =========================

@st.cache_data(show_spinner=False)
def load_depenses():
    res = (
        supabase
        .table("depenses")
        .select(
            """
            depense_id,
            date,
            annee,
            poste,
            compte,
            fournisseur,
            lot_id,
            montant_ttc,
            facture_url,
            pdf_url,
            commentaire,
            type,
            repartition_requise
            """
        )
        .execute()
    )
    return pd.DataFrame(res.data)

@st.cache_data(show_spinner=False)
def load_lots():
    res = (
        supabase
        .table("lots")
        .select(
            """
            lot_id,
            lot,
            batiment,
            etage,
            tantiemes,
            usage
            """
        )
        .execute()
    )
    return pd.DataFrame(res.data)

# =========================
# MAIN
# =========================

def main():
    st.title("📊 Pilotage des charges")

    df_dep = load_depenses()
    df_lots = load_lots()

    # Sécurité absolue
    if df_dep.empty:
        st.warning("Aucune dépense trouvée.")
        return

    # Harmonisation types pour merge
    df_dep["lot_id"] = df_dep["lot_id"].astype("Int64")
    df_lots["lot_id"] = df_lots["lot_id"].astype("Int64")

    # Merge PROPRE
    df = df_dep.merge(
        df_lots,
        on="lot_id",
        how="left"
    )

    # =========================
    # KPI
    # =========================

    c1, c2 = st.columns(2)

    with c1:
        st.metric("💸 Total des dépenses", euro(df["montant_ttc"].sum()))

    with c2:
        st.metric("🧾 Nombre de dépenses", len(df))

    st.divider()

    # =========================
    # TABLEAU
    # =========================

    df_display = df[
        [
            "date",
            "poste",
            "compte",
            "fournisseur",
            "montant_ttc",
            "lot",
            "batiment",
            "usage",
            "facture_url",
            "pdf_url",
            "commentaire"
        ]
    ].copy()

    df_display["montant_ttc"] = df_display["montant_ttc"].apply(euro)

    # Liens cliquables
    df_display["facture"] = df["facture_url"].apply(
        lambda x: f"[📎 Voir]({x})" if pd.notna(x) else ""
    )

    df_display["pdf"] = df["pdf_url"].apply(
        lambda x: f"[📄 PDF]({x})" if pd.notna(x) else ""
    )

    df_display = df_display.drop(columns=["facture_url", "pdf_url"])

    st.dataframe(
        df_display,
        use_container_width=True,
        hide_index=True
    )

# =========================
# RUN
# =========================

if __name__ == "__main__":
    main()