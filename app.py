import streamlit as st
import pandas as pd

# ======================================================
# CONFIG
# ======================================================
st.set_page_config(page_title="Pilotage des charges", layout="wide")
st.title("Pilotage des charges de l’immeuble")

# ======================================================
# NORMALISATION DES DONNÉES
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
    df["montant_ttc"] = df["montant_ttc"].astype(float)
    return df


def normalize_budget(df: pd.DataFrame) -> pd.DataFrame:
    df = df.rename(columns={
        "Annee": "annee",
        "compte": "compte",
        "budget": "budget",
    })
    df["annee"] = df["annee"].astype(float).astype(int)
    df["compte"] = df["compte"].astype(str)
    df["budget"] = df["budget"].astype(float)

    # règle comptable : 621 / 622 sur 4 chiffres, sinon 3
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
# NAVIGATION
# ======================================================
with st.sidebar:
    page = st.radio(
        "Navigation",
        [
            "📊 État des dépenses",
            "💰 Budget",
            "📊 Budget vs Réel – Pilotage",
        ]
    )

# ======================================================
# 📊 ONGLET 1 — ÉTAT DES DÉPENSES
# ======================================================
if page == "📊 État des dépenses":

    annee = st.selectbox("Année", sorted(df_dep["annee"].unique()))
    df_a = df_dep[df_dep["annee"] == annee].copy()

    dep_pos = df_a[df_a["montant_ttc"] > 0]
    dep_neg = df_a[df_a["montant_ttc"] < 0]

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Dépenses brutes (€)", f"{dep_pos['montant_ttc'].sum():,.2f}".replace(",", " "))
    col2.metric("Avoirs (€)", f"{dep_neg['montant_ttc'].sum():,.2f}".replace(",", " "))
    col3.metric("Dépenses nettes (€)", f"{df_a['montant_ttc'].sum():,.2f}".replace(",", " "))
    col4.metric("Fournisseurs", df_a["fournisseur"].nunique())

    st.markdown("### ✏️ Ajouter / Modifier / Supprimer des dépenses")

    df_edit = st.data_editor(df_a, num_rows="dynamic", use_container_width=True)

    df_other = df_dep[df_dep["annee"] != annee]
    st.session_state.df_depenses = pd.concat([df_other, df_edit], ignore_index=True)

    st.markdown("### 💾 Sauvegarde")
    st.download_button(
        "📥 Télécharger les dépenses",
        st.session_state.df_depenses.to_csv(index=False).encode("utf-8"),
        file_name="base_depenses_immeuble.csv",
        mime="text/csv",
    )

# ======================================================
# 💰 ONGLET 2 — BUDGET
# ======================================================
if page == "💰 Budget":

    annee_b = st.selectbox("Année budgétaire", sorted(df_budget["annee"].unique()))
    dfb = df_budget[df_budget["annee"] == annee_b].copy()

    col1, col2, col3 = st.columns(3)
    col1.metric("Budget total (€)", f"{dfb['budget'].sum():,.2f}".replace(",", " "))
    col2.metric("Comptes budgétés", len(dfb))
    col3.metric("Groupes", dfb["compte"].str[:2].nunique())

    st.markdown("### ✏️ Ajouter / Modifier / Supprimer le budget")

    df_edit = st.data_editor(dfb, num_rows="dynamic", use_container_width=True)

    df_other = df_budget[df_budget["annee"] != annee_b]
    st.session_state.df_budget = pd.concat([df_other, df_edit], ignore_index=True)

    st.markdown("### 💾 Sauvegarde")
    st.download_button(
        "📥 Télécharger le budget",
        st.session_state.df_budget.to_csv(index=False).encode("utf-8"),
        file_name="budget_comptes_generaux.csv",
        mime="text/csv",
    )

# ======================================================
# 📊 ONGLET 3 — BUDGET VS RÉEL
# ======================================================
if page == "📊 Budget vs Réel – Pilotage":

    st.subheader("📊 Budget vs Réel – Pilotage")

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

    if bud.empty:
        st.warning("Aucun compte budgété pour ce filtre.")
        st.stop()

    cles_budget = sorted(bud["compte"].unique(), key=len, reverse=True)

    def map_budget(compte):
        for cle in cles_budget:
            if str(compte).startswith(cle):
                return cle
        return "NON BUDGÉTÉ"

    dep["compte_budget"] = dep["compte"].apply(map_budget)

    dep_pos = dep[dep["montant_ttc"] > 0]
    dep_neg = dep[dep["montant_ttc"] < 0]

    reel_dep = dep_pos.groupby("compte_budget")["montant_ttc"].sum().reset_index(name="reel_depenses")
    avoirs = dep_neg.groupby("compte_budget")["montant_ttc"].sum().reset_index(name="avoirs")

    comp = bud.merge(reel_dep, left_on="compte", right_on="compte_budget", how="left")
    comp = comp.merge(avoirs, left_on="compte", right_on="compte_budget", how="left")

    comp["reel_depenses"] = comp["reel_depenses"].fillna(0)
    comp["avoirs"] = comp["avoirs"].fillna(0)
    comp["reel_net"] = comp["reel_depenses"] + comp["avoirs"]

    comp["ecart_eur"] = comp["reel_net"] - comp["budget"]
    comp["ecart_pct"] = comp.apply(
        lambda r: (r["ecart_eur"] / r["budget"] * 100) if r["budget"] != 0 else 0,
        axis=1,
    )

    if only_over:
        comp = comp[comp["ecart_eur"] > 0]

    total_budget = comp["budget"].sum()
    total_reel = comp["reel_net"].sum()
    total_avoirs = comp["avoirs"].sum()

    col1, col2, col3, col4, col5 = st.columns(5)
    col1.metric("Budget (€)", f"{total_budget:,.0f}".replace(",", " "))
    col2.metric("Dépenses nettes (€)", f"{total_reel:,.0f}".replace(",", " "))
    col3.metric("Avoirs (€)", f"{total_avoirs:,.0f}".replace(",", " "))
    col4.metric("Écart (€)", f"{(total_reel - total_budget):,.0f}".replace(",", " "))
    col5.metric(
        "Écart (%)",
        f"{((total_reel - total_budget) / total_budget * 100):.1f} %" if total_budget != 0 else "-"
    )

    st.markdown("### Détail Budget vs Réel")
    st.dataframe(
        comp[
            [
                "compte",
                "budget",
                "reel_depenses",
                "avoirs",
                "reel_net",
                "ecart_eur",
                "ecart_pct",
            ]
        ],
        use_container_width=True,
    )

# ======================================================
# FOOTER
# ======================================================
st.markdown("---")
st.caption("Outil de pilotage – Conseil syndical / Copropriété")
