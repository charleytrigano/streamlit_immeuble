import streamlit as st
import pandas as pd

# ======================================================
# CONFIG
# ======================================================
st.set_page_config(page_title="Pilotage des charges", layout="wide")
st.title("Pilotage des charges de l’immeuble")

# ======================================================
# NORMALISATION (ALIGNÉE SUR VOS CSV)
# ======================================================
def normalize_depenses(df: pd.DataFrame) -> pd.DataFrame:
    df = df.rename(columns={
        "Annee": "annee",
        "Compte": "compte",
        "Poste": "poste",
        "Fournisseur": "fournisseur",
        "Date": "date",
        "Montant TTC": "montant_ttc",
        "Type": "type",
        "Recurrent": "recurrent",
        "Commentaire": "commentaire",
    })
    df["annee"] = df["annee"].astype(float).astype(int)
    df["compte"] = df["compte"].astype(str)
    return df


def normalize_budget(df: pd.DataFrame) -> pd.DataFrame:
    df = df.rename(columns={
        "Annee": "annee",
        "compte": "compte",
        "budget": "budget",
    })
    df["annee"] = df["annee"].astype(float).astype(int)
    df["compte"] = df["compte"].astype(str)
    df["compte"] = df["compte"].apply(
        lambda x: x[:4] if x.startswith(("621", "622")) else x[:3]
    )
    return df

# ======================================================
# SESSION STATE
# ======================================================
if "df_depenses" not in st.session_state:
    st.session_state.df_depenses = None

if "df_budget" not in st.session_state:
    st.session_state.df_budget = None

# ======================================================
# SIDEBAR — CHARGEMENT
# ======================================================
with st.sidebar:
    st.markdown("## 📂 Chargement des données")

    dep_csv = st.file_uploader("Dépenses (CSV)", type="csv")
    bud_csv = st.file_uploader("Budget (CSV)", type="csv")

    if dep_csv:
        st.session_state.df_depenses = normalize_depenses(pd.read_csv(dep_csv))
        st.success("Dépenses chargées")

    if bud_csv:
        st.session_state.df_budget = normalize_budget(pd.read_csv(bud_csv))
        st.success("Budget chargé")

# ======================================================
# STOP SI DONNÉES MANQUANTES
# ======================================================
if st.session_state.df_depenses is None or st.session_state.df_budget is None:
    st.info("Veuillez charger les dépenses et le budget.")
    st.stop()

df_dep = st.session_state.df_depenses
df_budget = st.session_state.df_budget

# ======================================================
# NAVIGATION — OBLIGATOIRE AVANT USAGE
# ======================================================
with st.sidebar:
    page = st.radio(
        "Navigation",
        [
            "📊 État des dépenses",
            "💰 Budget",
            "📊 Budget vs Réel – Analyse",
        ]
    )

# ======================================================
# 📊 ONGLET 1 — ÉTAT DES DÉPENSES (ÉDITABLE)
# ======================================================
if page == "📊 État des dépenses":

    annee = st.selectbox("Année", sorted(df_dep["annee"].unique()))
    df_a = df_dep[df_dep["annee"] == annee].copy()

    # KPI
    col1, col2, col3 = st.columns(3)
    col1.metric("Total (€)", f"{df_a['montant_ttc'].sum():,.2f}".replace(",", " "))
    col2.metric("Lignes", len(df_a))
    col3.metric("Fournisseurs", df_a["fournisseur"].nunique())

    st.markdown("### ✏️ Ajouter / Modifier / Supprimer des dépenses")

    df_edit = st.data_editor(
        df_a,
        num_rows="dynamic",
        use_container_width=True
    )

    # Reconstruction globale
    df_other = df_dep[df_dep["annee"] != annee]
    st.session_state.df_depenses = pd.concat(
        [df_other, df_edit],
        ignore_index=True
    )

    # Sauvegarde volontaire
    st.markdown("### 💾 Sauvegarde")
    csv = st.session_state.df_depenses.to_csv(index=False).encode("utf-8")
    st.download_button(
        "📥 Télécharger les dépenses",
        csv,
        file_name="base_depenses_immeuble.csv",
        mime="text/csv"
    )

# ======================================================
# 💰 ONGLET 2 — BUDGET (ÉDITABLE)
# ======================================================
if page == "💰 Budget":

    annee_b = st.selectbox("Année budgétaire", sorted(df_budget["annee"].unique()))
    dfb = df_budget[df_budget["annee"] == annee_b].copy()

    # KPI TOUJOURS SUR LA BASE COMPLÈTE
    budget_total = dfb["budget"].sum()

    col1, col2, col3 = st.columns(3)
    col1.metric("Budget total (€)", f"{budget_total:,.2f}".replace(",", " "))
    col2.metric("Comptes budgétés", len(dfb))
    col3.metric("Groupes", dfb["compte"].str[:2].nunique())

    st.markdown("### ✏️ Ajouter / Modifier / Supprimer le budget")

    df_edit = st.data_editor(
        dfb,
        num_rows="dynamic",
        use_container_width=True
    )

    df_other = df_budget[df_budget["annee"] != annee_b]
    st.session_state.df_budget = pd.concat(
        [df_other, df_edit],
        ignore_index=True
    )

    st.markdown("### 💾 Sauvegarde")
    csv = st.session_state.df_budget.to_csv(index=False).encode("utf-8")
    st.download_button(
        "📥 Télécharger le budget",
        csv,
        file_name="budget_comptes_generaux.csv",
        mime="text/csv"
    )

# ======================================================
# 📊 ONGLET 3 — BUDGET VS RÉEL (PILOTAGE)
# ======================================================
if page == "📊 Budget vs Réel – Analyse":

    st.subheader("📊 Budget vs Réel – Pilotage")

    # Filtres
    colf1, colf2, colf3 = st.columns(3)

    with colf1:
        annee = st.selectbox("Année", sorted(df_dep["annee"].unique()))

    with colf2:
        groupes = sorted(df_budget["compte"].str[:2].unique())
        groupe_sel = st.selectbox("Groupe de comptes", ["Tous"] + groupes)

    with colf3:
        only_over = st.checkbox("Uniquement les dépassements")

    dep = df_dep[df_dep["annee"] == annee].copy()
    bud = df_budget[df_budget["annee"] == annee].copy()

    if groupe_sel != "Tous":
        bud = bud[bud["compte"].str.startswith(groupe_sel)]

    # Mapping budget → réel
    cles_budget = sorted(bud["compte"].unique(), key=len, reverse=True)

    def map_budget(compte):
        for cle in cles_budget:
            if str(compte).startswith(cle):
                return cle
        return "NON BUDGÉTÉ"

    dep["compte_budget"] = dep["compte"].apply(map_budget)

    reel = (
        dep.groupby("compte_budget")["montant_ttc"]
        .sum()
        .reset_index(name="reel")
    )

    comp = bud.merge(
        reel,
        left_on="compte",
        right_on="compte_budget",
        how="left"
    )

    comp["reel"] = comp["reel"].fillna(0)
    comp["ecart_eur"] = comp["reel"] - comp["budget"]
    comp["ecart_pct"] = comp.apply(
        lambda r: (r["ecart_eur"] / r["budget"] * 100)
        if r["budget"] != 0 else 0,
        axis=1
    )

    if only_over:
        comp = comp[comp["ecart_eur"] > 0]

    # KPI
    col1, col2, col3, col4, col5 = st.columns(5)

    total_budget = comp["budget"].sum()
    total_reel = comp["reel"].sum()
    total_ecart = total_reel - total_budget

    col1.metric("Budget (€)", f"{total_budget:,.0f}".replace(",", " "))
    col2.metric("Réel (€)", f"{total_reel:,.0f}".replace(",", " "))
    col3.metric("Écart (€)", f"{total_ecart:,.0f}".replace(",", " "))
    col4.metric(
        "Écart (%)",
        f"{(total_ecart / total_budget * 100):.1f} %" if total_budget != 0 else "-"
    )
    col5.metric("Comptes en dépassement", int((comp["ecart_eur"] > 0).sum()))

    st.markdown("### Détail Budget vs Réel")
    st.dataframe(
        comp[["compte", "budget", "reel", "ecart_eur", "ecart_pct"]],
        use_container_width=True
    )

# ======================================================
# FOOTER
# ======================================================
st.markdown("---")
st.caption("Outil de pilotage – Conseil syndical / Copropriété")
