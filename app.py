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
        return "0,00 €"
    return f"{x:,.2f} €".replace(",", " ").replace(".", ",")

# =========================
# DATA LOAD
# =========================
@st.cache_data(ttl=300)
def load_depenses():
    res = supabase.table("depenses").select(
        "date, annee, poste, compte, fournisseur, lot, montant_ttc, facture_url, commentaire"
    ).execute()
    return pd.DataFrame(res.data)

@st.cache_data(ttl=300)
def load_lots():
    res = supabase.table("lots").select(
        "lot, batiment, etage, tantiemes"
    ).execute()
    return pd.DataFrame(res.data)

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
    # NORMALISATION
    # =========================
    df_dep["lot"] = df_dep["lot"].astype(str).str.strip()
    df_lots["lot"] = df_lots["lot"].astype(str).str.strip()

    df_dep["montant_ttc"] = pd.to_numeric(df_dep["montant_ttc"], errors="coerce")

    # =========================
    # MERGE PROPRE (SUR CLÉ MÉTIER)
    # =========================
    df = df_dep.merge(
        df_lots,
        on="lot",
        how="left"
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
            "etage",
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
            "etage": "Étage",
            "tantiemes": "Tantièmes",
            "montant_ttc": "Montant TTC",
            "facture_url": "Facture",
            "commentaire": "Commentaire",
        }
    )

    df_display["Facture"] = df_display["Facture"].apply(
        lambda x: f"[📄 Voir]({x})" if pd.notna(x) and x != "" else ""
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