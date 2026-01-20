import streamlit as st
import pandas as pd
import unicodedata

# ======================================================
# CONFIG
# ======================================================
st.set_page_config(page_title="Pilotage des charges", layout="wide")
st.title("Pilotage des charges de l’immeuble")

# ======================================================
# OUTILS
# ======================================================
def clean_columns(df):
    def norm(c):
        c = str(c).strip().lower()
        c = unicodedata.normalize("NFKD", c).encode("ascii", "ignore").decode()
        return c.replace(" ", "_")
    df.columns = [norm(c) for c in df.columns]
    return df


def make_facture_link(url):
    if not url or str(url).lower() == "nan":
        return "—"
    return f'<a href="{url}" target="_blank">📄 Ouvrir</a>'


# ======================================================
# NORMALISATION
# ======================================================
def normalize_depenses(df):
    df = clean_columns(df)

    for col in ["poste", "fournisseur", "piece_id", "pdf_url"]:
        if col not in df.columns:
            df[col] = ""

    required = {"annee", "compte", "montant_ttc"}
    if not required.issubset(df.columns):
        st.error(f"Colonnes manquantes dans les dépenses : {required - set(df.columns)}")
        st.stop()

    df["annee"] = df["annee"].astype(float).astype(int)
    df["compte"] = df["compte"].astype(str)
    df["montant_ttc"] = df["montant_ttc"].astype(float)
    df["pdf_url"] = df["pdf_url"].astype(str).str.strip()

    df["statut_facture"] = df["pdf_url"].apply(
        lambda x: "Justifiée" if x not in ("", "nan", None) else "À justifier"
    )

    df["groupe_compte"] = df["compte"].apply(
        lambda x: x[:4] if x.startswith(("621", "622")) else x[:3]
    )

    return df


def normalize_budget(df):
    df = clean_columns(df)

    required = {"annee", "compte", "budget"}
    if not required.issubset(df.columns):
        st.error(f"Colonnes manquantes dans le budget : {required - set(df.columns)}")
        st.stop()

    df["annee"] = df["annee"].astype(float).astype(int)
    df["budget"] = df["budget"].astype(float)
    df["compte"] = df["compte"].astype(str)

    df["groupe_compte"] = df["compte"].apply(
        lambda x: x[:4] if x.startswith(("621", "622")) else x[:3]
    )

    return df


# ======================================================
# SESSION STATE
# ======================================================
if "df_dep" not in st.session_state:
    st.session_state.df_dep = None
if "df_bud" not in st.session_state:
    st.session_state.df_bud = None


# ======================================================
# SIDEBAR — CHARGEMENT CSV
# ======================================================
with st.sidebar:
    st.markdown("## 📂 Chargement des données")

    dep_csv = st.file_uploader("Dépenses (CSV)", type="csv", key="depenses")
    bud_csv = st.file_uploader("Budget (CSV)", type="csv", key="budget")

    if dep_csv:
        df = pd.read_csv(dep_csv, sep=None, engine="python", on_bad_lines="skip", encoding="utf-8-sig")
        st.session_state.df_dep = normalize_depenses(df)
        st.success("Dépenses chargées")

    if bud_csv:
        df = pd.read_csv(bud_csv, sep=None, engine="python", on_bad_lines="skip", encoding="utf-8-sig")
        st.session_state.df_bud = normalize_budget(df)
        st.success("Budget chargé")

if st.session_state.df_dep is None or st.session_state.df_bud is None:
    st.info("Veuillez charger les dépenses et le budget.")
    st.stop()

df_dep = st.session_state.df_dep
df_bud = st.session_state.df_bud


# ======================================================
# NAVIGATION
# ======================================================
page = st.sidebar.radio(
    "Navigation",
    ["📊 État des dépenses", "💰 Budget", "📊 Budget vs Réel"]
)

# ======================================================
# 📊 ÉTAT DES DÉPENSES — FILTRES COMPLETS
# ======================================================
if page == "📊 État des dépenses":

    st.markdown("### 🔎 Filtres")

    colf1, colf2, colf3, colf4 = st.columns(4)

    with colf1:
        annee = st.selectbox("Année", sorted(df_dep["annee"].unique()))
    with colf2:
        groupes = ["Tous"] + sorted(df_dep["groupe_compte"].unique())
        groupe = st.selectbox("Groupe de comptes", groupes)
    with colf3:
        fournisseurs = ["Tous"] + sorted(df_dep["fournisseur"].unique())
        fournisseur = st.selectbox("Fournisseur", fournisseurs)
    with colf4:
        statuts = ["Tous", "Justifiée", "À justifier"]
        statut = st.selectbox("Statut facture", statuts)

    df_f = df_dep[df_dep["annee"] == annee].copy()

    if groupe != "Tous":
        df_f = df_f[df_f["groupe_compte"] == groupe]
    if fournisseur != "Tous":
        df_f = df_f[df_f["fournisseur"] == fournisseur]
    if statut != "Tous":
        df_f = df_f[df_f["statut_facture"] == statut]

    df_f["Facture"] = df_f["pdf_url"].apply(make_facture_link)
    df_f["Montant (€)"] = df_f["montant_ttc"].map(lambda x: f"{x:,.2f}".replace(",", " "))

    dep_pos = df_f[df_f["montant_ttc"] > 0]["montant_ttc"].sum()
    dep_neg = df_f[df_f["montant_ttc"] < 0]["montant_ttc"].sum()

    k1, k2, k3, k4 = st.columns(4)
    k1.metric("Dépenses brutes (€)", f"{dep_pos:,.0f}".replace(",", " "))
    k2.metric("Avoirs (€)", f"{dep_neg:,.0f}".replace(",", " "))
    k3.metric("Dépenses nettes (€)", f"{dep_pos + dep_neg:,.0f}".replace(",", " "))
    k4.metric("% justifiées", f"{(df_f['statut_facture'].eq('Justifiée').mean()*100):.0f} %")

    st.markdown("### 📋 Détail des dépenses")

    df_table = df_f[
        [
            "compte",
            "poste",
            "fournisseur",
            "Montant (€)",
            "statut_facture",
            "Facture",
        ]
    ]

    st.markdown(
        df_table.to_html(escape=False, index=False),
        unsafe_allow_html=True
    )


# ======================================================
# 💰 BUDGET
# ======================================================
if page == "💰 Budget":

    annee = st.selectbox("Année budgétaire", sorted(df_bud["annee"].unique()))
    df_b = df_bud[df_bud["annee"] == annee].copy()

    st.metric("Budget total (€)", f"{df_b['budget'].sum():,.0f}".replace(",", " "))

    st.data_editor(df_b, num_rows="dynamic", use_container_width=True)


# ======================================================
# 📊 BUDGET VS RÉEL — FILTRES + KPI
# ======================================================
if page == "📊 Budget vs Réel":

    st.markdown("### 🔎 Filtres")

    colf1, colf2 = st.columns(2)
    with colf1:
        annee = st.selectbox("Année", sorted(df_dep["annee"].unique()))
    with colf2:
        afficher_depassements = st.checkbox("Uniquement les dépassements")

    dep = df_dep[df_dep["annee"] == annee].copy()
    bud = df_bud[df_bud["annee"] == annee].copy()

    reel = dep.groupby("groupe_compte")["montant_ttc"].sum().reset_index()
    comp = bud.merge(reel, on="groupe_compte", how="left").fillna(0)

    comp["écart (€)"] = comp["montant_ttc"] - comp["budget"]
    comp["écart (%)"] = (comp["écart (€)"] / comp["budget"] * 100).round(1)

    if afficher_depassements:
        comp = comp[comp["écart (€)"] > 0]

    k1, k2, k3 = st.columns(3)
    k1.metric("Budget total (€)", f"{comp['budget'].sum():,.0f}".replace(",", " "))
    k2.metric("Réel (€)", f"{comp['montant_ttc'].sum():,.0f}".replace(",", " "))
    k3.metric("Écart (€)", f"{comp['écart (€)'].sum():,.0f}".replace(",", " "))

    st.markdown("### 📊 Comparaison Budget vs Réel")

    st.dataframe(
        comp[
            [
                "groupe_compte",
                "budget",
                "montant_ttc",
                "écart (€)",
                "écart (%)",
            ]
        ],
        use_container_width=True,
    )
