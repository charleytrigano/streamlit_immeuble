import streamlit as st
import pandas as pd
import unicodedata

# ======================================================
# CONFIG
# ======================================================
st.set_page_config(page_title="Pilotage des charges", layout="wide")
st.title("Pilotage des charges de l’immeuble")

DEP_FILE = "data/base_depenses_immeuble.csv"
BUD_FILE = "data/budget_comptes_generaux.csv"

# ======================================================
# OUTILS
# ======================================================
def clean_columns(df):
    def norm(c):
        c = str(c).strip().lower()
        c = unicodedata.normalize("NFKD", c).encode("ascii", "ignore").decode()
        return c.replace(" ", "_").replace("-", "_")
    df.columns = [norm(c) for c in df.columns]
    return df


def load_depenses():
    df = pd.read_csv(DEP_FILE, sep=",", encoding="utf-8-sig")
    df = clean_columns(df)
    df["annee"] = df["annee"].astype(int)
    df["compte"] = df["compte"].astype(str)
    df["montant_ttc"] = df["montant_ttc"].astype(float)
    df["pdf_url"] = df.get("pdf_url", "")
    return df


def load_budget():
    df = pd.read_csv(BUD_FILE, sep=",", encoding="utf-8-sig")
    df = clean_columns(df)
    df["annee"] = df["annee"].astype(int)
    df["compte"] = df["compte"].astype(str)
    df["budget"] = df["budget"].astype(float)
    df["groupe_compte"] = df.get("groupe_compte", df["compte"])
    return df


def google_link(url):
    if isinstance(url, str) and "/preview" in url:
        return url
    return None


# ======================================================
# CHARGEMENT DONNÉES
# ======================================================
if "df_dep" not in st.session_state:
    st.session_state.df_dep = load_depenses()

if "df_bud" not in st.session_state:
    st.session_state.df_bud = load_budget()

df_dep = st.session_state.df_dep
df_bud = st.session_state.df_bud

# ======================================================
# SIDEBAR
# ======================================================
with st.sidebar:
    st.markdown("## 📂 Données")
    if st.button("🔄 Recharger les données"):
        st.session_state.df_dep = load_depenses()
        st.session_state.df_bud = load_budget()
        st.experimental_rerun()

    page = st.radio(
        "Navigation",
        ["📊 État des dépenses", "💰 Budget", "📊 Budget vs Réel"]
    )

# ======================================================
# 📊 ÉTAT DES DÉPENSES
# ======================================================
if page == "📊 État des dépenses":

    annee = st.selectbox("Année", sorted(df_dep["annee"].unique()))
    fournisseurs = ["Tous"] + sorted(df_dep["fournisseur"].dropna().unique())

    fournisseur = st.selectbox("Fournisseur", fournisseurs)

    df_f = df_dep[df_dep["annee"] == annee].copy()
    if fournisseur != "Tous":
        df_f = df_f[df_f["fournisseur"] == fournisseur]

    dep_brutes = df_f[df_f["montant_ttc"] > 0]["montant_ttc"].sum()
    avoirs = df_f[df_f["montant_ttc"] < 0]["montant_ttc"].sum()
    net = dep_brutes + avoirs

    c1, c2, c3 = st.columns(3)
    c1.metric("Dépenses brutes (€)", f"{dep_brutes:,.0f}".replace(",", " "))
    c2.metric("Avoirs (€)", f"{avoirs:,.0f}".replace(",", " "))
    c3.metric("Dépenses nettes (€)", f"{net:,.0f}".replace(",", " "))

    def facture_cell(url):
        link = google_link(url)
        return "📄 Ouvrir" if link else "—"

    df_f["Facture"] = df_f["pdf_url"].apply(facture_cell)

    st.markdown("### 📋 Détail des dépenses")
    st.dataframe(
        df_f[
            ["compte", "poste", "fournisseur", "montant_ttc", "Facture"]
        ],
        use_container_width=True
    )

    # Bouton facture
    lignes_avec_facture = df_f[df_f["pdf_url"].apply(lambda x: google_link(x) is not None)]
    if not lignes_avec_facture.empty:
        idx = st.selectbox(
            "Ouvrir une facture",
            lignes_avec_facture.index,
            format_func=lambda i: f"{lignes_avec_facture.loc[i,'poste']} – {lignes_avec_facture.loc[i,'montant_ttc']} €"
        )
        st.link_button(
            "📄 Ouvrir la facture",
            lignes_avec_facture.loc[idx, "pdf_url"]
        )

# ======================================================
# 💰 BUDGET
# ======================================================
if page == "💰 Budget":

    annees = sorted(df_bud["annee"].unique())
    annee = st.selectbox("Année budgétaire", annees)

    df_a = df_bud[df_bud["annee"] == annee].copy()
    st.metric("Budget total (€)", f"{df_a['budget'].sum():,.0f}".replace(",", " "))

    st.markdown("### ✏️ Modifier le budget")
    df_edit = st.data_editor(
        df_a,
        num_rows="dynamic",
        use_container_width=True
    )

    df_autres = df_bud[df_bud["annee"] != annee]
    df_final = pd.concat([df_autres, df_edit], ignore_index=True)

    st.download_button(
        "💾 Télécharger budget_comptes_generaux.csv",
        df_final.to_csv(index=False).encode("utf-8"),
        file_name="budget_comptes_generaux.csv",
        mime="text/csv"
    )

    st.markdown("### ➕ Créer un nouveau budget")
    col1, col2 = st.columns(2)
    with col1:
        annee_source = st.selectbox("Année source", annees)
    with col2:
        annee_cible = st.number_input("Nouvelle année", min_value=2000, max_value=2100, step=1)

    if st.button("📄 Créer le nouveau budget"):
        if annee_cible in annees:
            st.error("Cette année existe déjà.")
        else:
            base = df_bud[df_bud["annee"] == annee_source].copy()
            base["annee"] = annee_cible
            df_new = pd.concat([df_bud, base], ignore_index=True)

            st.download_button(
                "💾 Télécharger le nouveau budget",
                df_new.to_csv(index=False).encode("utf-8"),
                file_name="budget_comptes_generaux.csv",
                mime="text/csv"
            )
            st.success("Télécharge le fichier puis remplace-le dans GitHub.")

# ======================================================
# 📊 BUDGET VS RÉEL
# ======================================================
if page == "📊 Budget vs Réel":

    annee = st.selectbox("Année", sorted(df_dep["annee"].unique()))

    dep = df_dep[df_dep["annee"] == annee].copy()
    bud = df_bud[df_bud["annee"] == annee].copy()

    dep["groupe"] = dep["compte"].str[:3]

    dep_grp = dep.groupby("groupe")["montant_ttc"].sum().reset_index(name="reel")
    bud_grp = bud.groupby("groupe_compte")["budget"].sum().reset_index()

    comp = bud_grp.merge(
        dep_grp,
        left_on="groupe_compte",
        right_on="groupe",
        how="left"
    ).fillna(0)

    comp["ecart_eur"] = comp["reel"] - comp["budget"]
    comp["ecart_pct"] = (comp["ecart_eur"] / comp["budget"] * 100).round(1)

    c1, c2, c3 = st.columns(3)
    c1.metric("Budget (€)", f"{comp['budget'].sum():,.0f}".replace(",", " "))
    c2.metric("Réel (€)", f"{comp['reel'].sum():,.0f}".replace(",", " "))
    c3.metric("Écart (€)", f"{comp['ecart_eur'].sum():,.0f}".replace(",", " "))

    st.markdown("### 📊 Détail Budget vs Réel")
    st.dataframe(
        comp[
            ["groupe_compte", "budget", "reel", "ecart_eur", "ecart_pct"]
        ],
        use_container_width=True
    )