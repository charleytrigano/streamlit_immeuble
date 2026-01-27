import streamlit as st
import pandas as pd
from supabase import create_client

# =========================
# CONFIG
# =========================
st.set_page_config(page_title="Pilotage des charges", layout="wide")

SUPABASE_URL = st.secrets["SUPABASE_URL"]
SUPABASE_KEY = st.secrets["SUPABASE_ANON_KEY"]

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# =========================
# UTILS
# =========================
def euro(x):
    if pd.isna(x):
        return "0 €"
    return f"{x:,.2f} €".replace(",", " ").replace(".", ",")

# =========================
# DATA LOAD
# =========================
@st.cache_data(ttl=300)
def load_depenses():
    res = supabase.table("depenses").select("*").execute()
    df = pd.DataFrame(res.data)
    return df

@st.cache_data(ttl=300)
def load_lots():
    res = supabase.table("lots").select("*").execute()
    df = pd.DataFrame(res.data)
    return df

# =========================
# MAIN
# =========================
def main():
    st.title("📊 Pilotage des charges")

    df_dep = load_depenses()
    df_lots = load_lots()

    if df_dep.empty:
        st.warning("Aucune dépense trouvée")
        return

    # =========================
    # NORMALISATION TYPES (OBLIGATOIRE)
    # =========================
    df_dep["lot_id"] = df_dep["lot_id"].astype(str)
    df_lots["lot_id"] = df_lots["lot_id"].astype(str)

    df_dep["montant_ttc"] = pd.to_numeric(df_dep["montant_ttc"], errors="coerce")

    # =========================
    # MERGE
    # =========================
    df = df_dep.merge(
        df_lots,
        on="lot_id",
        how="left",
        suffixes=("", "_lot")
    )

    # =========================
    # KPI
    # =========================
    c1, c2 = st.columns(2)
    c1.metric("💸 Total des dépenses", euro(df["montant_ttc"].sum()))
    c2.metric("🧾 Nombre de dépenses", len(df))

    st.divider()

    # =========================
    # TABLEAU AFFICHAGE
    # =========================
    df_display = df[
        [
            "date",
            "annee",
            "poste",
            "compte",
            "fournisseur",
            "lot",
            "batiment",
            "tantiemes",
            "montant_ttc",
            "facture_url",
            "commentaire",
        ]
    ].copy()

    df_display = df_display.rename(
        columns={
            "date": "Date",
            "annee": "Année",
            "poste": "Poste",
            "compte": "Compte",
            "fournisseur": "Fournisseur",
            "lot": "Lot",
            "batiment": "Bâtiment",
            "tantiemes": "Tantièmes",
            "montant_ttc": "Montant TTC",
            "facture_url": "Facture",
            "commentaire": "Commentaire",
        }
    )

    df_display["Facture"] = df_display["Facture"].apply(
        lambda x: f"[Voir]({x})" if pd.notna(x) and x != "" else ""
    )

    df_display["Montant TTC"] = df_display["Montant TTC"].apply(euro)

    st.dataframe(
        df_display,
        use_container_width=True,
        hide_index=True,
    )

# =========================
# RUN
# =========================
if __name__ == "__main__":
    main()