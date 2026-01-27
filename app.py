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
    if val is None:
        return "0 €"
    return f"{val:,.2f} €".replace(",", " ").replace(".", ",")


def load_table(table_name):
    res = supabase.table(table_name).select("*").execute()
    if not res.data:
        return pd.DataFrame()
    return pd.DataFrame(res.data)


# =========================
# APP
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

    total_depenses = df_dep["montant_ttc"].sum()

    col1, col2 = st.columns(2)
    col1.metric("💸 Total des dépenses", euro(total_depenses))
    col2.metric("🧾 Nombre de dépenses", len(df_dep))

    st.divider()

    # =========================
    # JOIN AVEC LOTS
    # =========================

    df_display = df_dep.merge(
        df_lots,
        left_on="lot_id",
        right_on="id",
        how="left",
        suffixes=("", "_lot")
    )

    # =========================
    # LIEN FACTURE
    # =========================

    def build_facture_link(row):
        if pd.notna(row.get("pdf_url")):
            return f"[📄 Voir]({row['pdf_url']})"
        if pd.notna(row.get("facture_url")):
            return f"[📄 Voir]({row['facture_url']})"
        return ""

    df_display["facture"] = df_display.apply(build_facture_link, axis=1)

    # =========================
    # TABLE FINALE
    # =========================

    columns = [
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

    df_display = df_display[columns].sort_values("date", ascending=False)

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