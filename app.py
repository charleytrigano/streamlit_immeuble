import streamlit as st
import pandas as pd
from supabase import create_client

# =========================
# CONFIG
# =========================

SUPABASE_URL = st.secrets["SUPABASE_URL"]
SUPABASE_KEY = st.secrets["SUPABASE_ANON_KEY"]

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

st.set_page_config(page_title="Pilotage des charges", layout="wide")


# =========================
# HELPERS
# =========================

def euro(val):
    if val is None or pd.isna(val):
        return "0 €"
    return f"{val:,.2f} €".replace(",", " ").replace(".", ",")


def load_table(name):
    res = supabase.table(name).select("*").execute()
    return pd.DataFrame(res.data) if res.data else pd.DataFrame()


# =========================
# MAIN
# =========================

def main():
    st.title("📊 Pilotage des charges")

    # =========================
    # LOAD DATA
    # =========================

    df_dep = load_table("depenses")
    df_lots = load_table("lots")

    if df_dep.empty:
        st.warning("Aucune dépense trouvée")
        return

    # =========================
    # METRICS
    # =========================

    col1, col2 = st.columns(2)
    col1.metric("💸 Total des dépenses", euro(df_dep["montant_ttc"].sum()))
    col2.metric("🧾 Nombre de dépenses", len(df_dep))

    st.divider()

    # =========================
    # MERGE CORRECT (clé réelle)
    # =========================

    df = df_dep.merge(
        df_lots,
        on="lot_id",          # ✅ clé réelle des deux tables
        how="left",
        suffixes=("", "_lot")
    )

    # =========================
    # FACTURE LINK
    # =========================

    def facture_link(row):
        if pd.notna(row.get("pdf_url")):
            return f"[📄 Voir]({row['pdf_url']})"
        if pd.notna(row.get("facture_url")):
            return f"[📄 Voir]({row['facture_url']})"
        return ""

    df["facture"] = df.apply(facture_link, axis=1)

    # =========================
    # TABLE AFFICHÉE
    # =========================

    df_display = df[
        [
            "date",
            "poste",
            "fournisseur",
            "compte",
            "type",
            "montant_ttc",
            "lot",
            "batiment",
            "tantiemes",
            "commentaire",
            "facture",
        ]
    ].sort_values("date", ascending=False)

    st.subheader("📋 Détail des dépenses")

    st.dataframe(
        df_display,
        use_container_width=True,
        column_config={
            "montant_ttc": st.column_config.NumberColumn(
                "Montant TTC",
                format="%.2f €"
            ),
            "facture": st.column_config.MarkdownColumn("Facture"),
        },
    )


if __name__ == "__main__":
    main()