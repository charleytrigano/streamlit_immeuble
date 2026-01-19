import streamlit as st
import pandas as pd
import unicodedata
import os

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

def facture_status(row):
    if pd.isna(row.get("piece_id")) or row["piece_id"] == "":
        return "❌ À justifier", None
    path = f"factures/{row['annee']}/{row['piece_id']}.pdf"
    if os.path.exists(path):
        return "✅ OK", path
    return "⚠️ PDF manquant", None

# ======================================================
# NORMALISATION
# ======================================================
def normalize_depenses(df):
    df = clean_columns(df)

    if "poste" not in df.columns:
        df["poste"] = "Non renseigné"
    if "fournisseur" not in df.columns:
        df["fournisseur"] = "Non renseigné"
    if "piece_id" not in df.columns:
        df["piece_id"] = ""

    required = {"annee", "compte", "montant_ttc"}
    if not required.issubset(df.columns):
        st.error(f"Colonnes manquantes dans les dépenses : {required - set(df.columns)}")
        st.stop()

    df["annee"] = df["annee"].astype(float).astype(int)
    df["compte"] = df["compte"].astype(str)
    df["montant_ttc"] = df["montant_ttc"].astype(float)
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

    df["compte"] = df["compte"].apply(
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

    dep_csv = st.file_uploader("Dépenses (CSV)", type="csv")
    bud_csv = st.file_uploader("Budget (CSV)", type="csv")

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
with st.sidebar:
    page = st.radio(
        "Navigation",
        ["📊 État des dépenses", "💰 Budget", "📊 Budget vs Réel"]
    )

# ======================================================
# 📊 ÉTAT DES DÉPENSES
# ======================================================
if page == "📊 État des dépenses":

    colf1, colf2, colf3 = st.columns(3)
    with colf1:
        annee = st.selectbox("Année", sorted(df_dep["annee"].unique()))
    with colf2:
        groupes = sorted(df_dep["compte"].str[:2].unique())
        groupe = st.selectbox("Groupe de comptes", ["Tous"] + groupes)
    with colf3:
        type_flux = st.selectbox("Type", ["Tous", "Dépenses", "Avoirs"])

    df_f = df_dep[df_dep["annee"] == annee].copy()

    if groupe != "Tous":
        df_f = df_f[df_f["compte"].str.startswith(groupe)]

    fournisseurs = ["Tous"] + sorted(df_f["fournisseur"].unique())
    postes = ["Tous"] + sorted(df_f["poste"].unique())

    colf4, colf5 = st.columns(2)
    with colf4:
        fournisseur = st.selectbox("Fournisseur", fournisseurs)
    with colf5:
        poste = st.selectbox("Poste", postes)

    if fournisseur != "Tous":
        df_f = df_f[df_f["fournisseur"] == fournisseur]
    if poste != "Tous":
        df_f = df_f[df_f["poste"] == poste]

    if type_flux == "Dépenses":
        df_f = df_f[df_f["montant_ttc"] > 0]
    elif type_flux == "Avoirs":
        df_f = df_f[df_f["montant_ttc"] < 0]

    dep_pos = df_f[df_f["montant_ttc"] > 0]["montant_ttc"].sum()
    dep_neg = df_f[df_f["montant_ttc"] < 0]["montant_ttc"].sum()

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Dépenses brutes (€)", f"{dep_pos:,.0f}".replace(",", " "))
    col2.metric("Avoirs (€)", f"{dep_neg:,.0f}".replace(",", " "))
    col3.metric("Dépenses nettes (€)", f"{dep_pos + dep_neg:,.0f}".replace(",", " "))
    col4.metric("Lignes", len(df_f))

    df_f[["statut_facture", "facture_path"]] = df_f.apply(
        lambda r: pd.Series(facture_status(r)), axis=1
    )

    st.markdown("### ✏️ Ajouter / Modifier / Supprimer des dépenses")

    df_edit = st.data_editor(
        df_f,
        num_rows="dynamic",
        use_container_width=True
    )

    df_other = df_dep.drop(df_f.index)
    st.session_state.df_dep = pd.concat([df_other, df_edit], ignore_index=True)

    st.download_button(
        "📥 Télécharger les dépenses",
        st.session_state.df_dep.to_csv(index=False).encode("utf-8"),
        file_name="base_depenses_immeuble.csv",
        mime="text/csv",
    )

    st.markdown("### 📄 Consulter une facture")

    factures_ok = df_f[df_f["facture_path"].notna()]
    if not factures_ok.empty:
        idx = st.selectbox(
            "Choisir une dépense",
            factures_ok.index,
            format_func=lambda i: f"{factures_ok.loc[i,'poste']} – {factures_ok.loc[i,'fournisseur']} – {factures_ok.loc[i,'montant_ttc']} €"
        )
        with open(factures_ok.loc[idx, "facture_path"], "rb") as f:
            st.download_button(
                "📄 Ouvrir la facture",
                f,
                file_name=os.path.basename(factures_ok.loc[idx, "facture_path"]),
                mime="application/pdf"
            )

# ======================================================
# 💰 BUDGET
# ======================================================
if page == "💰 Budget":

    annee = st.selectbox("Année budgétaire", sorted(df_bud["annee"].unique()))
    df_b = df_bud[df_bud["annee"] == annee].copy()

    col1, col2, col3 = st.columns(3)
    col1.metric("Budget total (€)", f"{df_b['budget'].sum():,.0f}".replace(",", " "))
    col2.metric("Comptes budgétés", len(df_b))
    col3.metric("Groupes", df_b["compte"].str[:2].nunique())

    st.markdown("### ✏️ Ajouter / Modifier / Supprimer le budget")

    df_edit = st.data_editor(
        df_b,
        num_rows="dynamic",
        use_container_width=True
    )

    df_other = df_bud[df_bud["annee"] != annee]
    st.session_state.df_bud = pd.concat([df_other, df_edit], ignore_index=True)

    st.download_button(
        "📥 Télécharger le budget",
        st.session_state.df_bud.to_csv(index=False).encode("utf-8"),
        file_name="budget_comptes_generaux.csv",
        mime="text/csv",
    )

# ======================================================
# 📊 BUDGET VS RÉEL
# ======================================================
if page == "📊 Budget vs Réel":

    colf1, colf2 = st.columns(2)
    with colf1:
        annee = st.selectbox("Année", sorted(df_dep["annee"].unique()))
    with colf2:
        only_over = st.checkbox("Uniquement les dépassements")

    dep = df_dep[df_dep["annee"] == annee].copy()
    bud = df_bud[df_bud["annee"] == annee].copy()

    cles = sorted(bud["compte"].unique(), key=len, reverse=True)

    def map_budget(c):
        for cle in cles:
            if c.startswith(cle):
                return cle
        return "NON BUDGÉTÉ"

    dep["compte_budget"] = dep["compte"].apply(map_budget)

    postes = (
        dep.groupby(["compte_budget", "poste"])
        .size()
        .reset_index(name="n")
        .sort_values(["compte_budget", "n"], ascending=[True, False])
        .drop_duplicates("compte_budget")
        .set_index("compte_budget")["poste"]
    )

    dep_pos = dep[dep["montant_ttc"] > 0].groupby("compte_budget")["montant_ttc"].sum()
    dep_neg = dep[dep["montant_ttc"] < 0].groupby("compte_budget")["montant_ttc"].sum()

    comp = bud.set_index("compte").copy()
    comp["poste"] = postes
    comp["depenses_brutes"] = dep_pos
    comp["avoirs"] = dep_neg
    comp = comp.fillna(0)

    comp["depenses_nettes"] = comp["depenses_brutes"] + comp["avoirs"]
    comp["ecart_eur"] = comp["depenses_nettes"] - comp["budget"]
    comp["ecart_pct"] = comp["ecart_eur"] / comp["budget"] * 100

    if only_over:
        comp = comp[comp["ecart_eur"] > 0]

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Budget (€)", f"{comp['budget'].sum():,.0f}".replace(",", " "))
    col2.metric("Réel net (€)", f"{comp['depenses_nettes'].sum():,.0f}".replace(",", " "))
    col3.metric("Écart (€)", f"{comp['ecart_eur'].sum():,.0f}".replace(",", " "))
    col4.metric(
        "Écart (%)",
        f"{(comp['ecart_eur'].sum() / comp['budget'].sum() * 100):.1f} %"
        if comp['budget'].sum() != 0 else "-"
    )

    st.markdown("### Détail Budget vs Réel")
    st.dataframe(
        comp.reset_index()[[
            "compte",
            "poste",
            "budget",
            "depenses_brutes",
            "avoirs",
            "depenses_nettes",
            "ecart_eur",
            "ecart_pct",
        ]],
        use_container_width=True,
    )
