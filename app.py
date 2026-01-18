import streamlit as st
import pandas as pd

# =========================
# CONFIG STREAMLIT
# =========================
st.set_page_config(
    page_title="Pilotage des charges – Immeuble",
    layout="wide"
)

st.title("Pilotage des charges de l’immeuble")
st.markdown(
    """
    Application de **pilotage budgétaire et contrôle des charges**
    à partir d’une **base CSV unique**.
    """
)

# =========================
# SESSION STATE
# =========================
if "df_factures" not in st.session_state:
    st.session_state.df_factures = None

if "df_budget" not in st.session_state:
    st.session_state.df_budget = pd.DataFrame(
        columns=["Année", "Poste", "Budget"]
    )

# =========================
# MODE COPROPRIÉTAIRE
# =========================
mode_copro = st.toggle(
    "Mode copropriétaire (lecture simplifiée)",
    value=False
)

# =========================
# IMPORT BASE CSV (DÉPENSES)
# =========================
st.markdown("## 📥 Import des dépenses (CSV)")

uploaded_csv = st.file_uploader(
    "Importer la base des dépenses (CSV)",
    type=["csv"]
)

if uploaded_csv:
    try:
        df = pd.read_csv(uploaded_csv, sep=None, engine="python")
        df.columns = [c.strip().replace("\ufeff", "") for c in df.columns]

        required_cols = [
            "Année", "Compte", "Poste", "Fournisseur",
            "Date", "Montant TTC"
        ]
        missing = [c for c in required_cols if c not in df.columns]

        if missing:
            st.error(f"Colonnes manquantes : {', '.join(missing)}")
        else:
            st.session_state.df_factures = df
            st.success("Dépenses chargées avec succès")

    except Exception as e:
        st.error(f"Erreur de lecture du CSV : {e}")

# =========================
# STOP SI PAS DE DONNÉES
# =========================
if st.session_state.df_factures is None:
    st.info("Veuillez importer une base CSV pour continuer.")
    st.stop()

df = st.session_state.df_factures

# =========================
# FILTRE ANNÉE
# =========================
annees = sorted(df["Année"].dropna().unique())
annee_sel = st.selectbox("Exercice analysé", annees)

df_annee = df[df["Année"] == annee_sel]

# =========================
# ✏️ ÉDITION DES DÉPENSES
# =========================
if not mode_copro:
    st.markdown("## ✏️ Édition des dépenses")

    st.markdown(
        "Vous pouvez **corriger, compléter ou ajouter des lignes**. "
        "Les modifications ne sont appliquées qu’après téléchargement."
    )

    df_edit = st.data_editor(
        df_annee,
        num_rows="dynamic",
        use_container_width=True
    )

    # Reconstruction base complète
    df_autres_annees = df[df["Année"] != annee_sel]
    df_final = pd.concat([df_autres_annees, df_edit], ignore_index=True)

    # Export CSV mis à jour
    export_depenses = f"depenses_corrigees_{annee_sel}.csv"
    df_final.to_csv(export_depenses, index=False, encoding="utf-8")

    with open(export_depenses, "rb") as f:
        st.download_button(
            "📥 Télécharger les dépenses mises à jour",
            f,
            file_name=export_depenses,
            mime="text/csv"
        )
else:
    df_final = df.copy()

# =========================
# 📊 SYNTHÈSE PAR POSTE
# =========================
st.markdown("## 📊 Synthèse des charges par poste")

synthese = (
    df_final[df_final["Année"] == annee_sel]
    .groupby("Poste")["Montant TTC"]
    .sum()
    .reset_index()
    .sort_values("Montant TTC", ascending=False)
)

st.dataframe(synthese, use_container_width=True)

total = synthese["Montant TTC"].sum()
top_poste = synthese.iloc[0]

st.info(
    f"Le poste **{top_poste['Poste']}** représente "
    f"{top_poste['Montant TTC'] / total * 100:.1f} % "
    f"des charges totales."
)

st.bar_chart(
    synthese.set_index("Poste")["Montant TTC"]
)

# =========================
# 💰 BUDGET – SAISIE & ÉDITION
# =========================
if not mode_copro:
    st.markdown("## 💰 Budget prévisionnel")

    uploaded_budget = st.file_uploader(
        "Importer un budget existant (CSV)",
        type=["csv"],
        key="budget_upload"
    )

    if uploaded_budget:
        try:
            st.session_state.df_budget = pd.read_csv(
                uploaded_budget, sep=None, engine="python"
            )
            st.session_state.df_budget.columns = [
                c.strip() for c in st.session_state.df_budget.columns
            ]
            st.success("Budget chargé")
        except Exception as e:
            st.error(f"Erreur budget : {e}")

    df_budget = st.session_state.df_budget

    df_budget_annee = df_budget[df_budget["Année"] == annee_sel]

    df_budget_edit = st.data_editor(
        df_budget_annee,
        num_rows="dynamic",
        use_container_width=True
    )

    df_budget_autres = df_budget[df_budget["Année"] != annee_sel]
    df_budget_final = pd.concat(
        [df_budget_autres, df_budget_edit],
        ignore_index=True
    )

    st.session_state.df_budget = df_budget_final

    budget_file = f"budget_{annee_sel}.csv"
    df_budget_final.to_csv(budget_file, index=False, encoding="utf-8")

    with open(budget_file, "rb") as f:
        st.download_button(
            "📥 Télécharger le budget mis à jour",
            f,
            file_name=budget_file,
            mime="text/csv"
        )

# =========================
# 📊 COMPARAISON BUDGET vs RÉEL
# =========================
if not mode_copro and not st.session_state.df_budget.empty:
    st.markdown("## 📊 Budget vs Réel")

    df_reel = synthese.copy()
    df_budget = st.session_state.df_budget
    df_budget_annee = df_budget[df_budget["Année"] == annee_sel]

    df_comp = df_reel.merge(
        df_budget_annee,
        on="Poste",
        how="left"
    )

    df_comp["Écart (€)"] = df_comp["Montant TTC"] - df_comp["Budget"]
    df_comp["Écart (%)"] = (
        df_comp["Écart (€)"] / df_comp["Budget"]
    ) * 100

    st.dataframe(df_comp, use_container_width=True)

# =========================
# 📈 PLURIANNUEL
# =========================
if df_final["Année"].nunique() >= 2:
    st.markdown("## 📈 Analyse pluriannuelle")

    evol = (
        df_final.groupby(["Année", "Poste"])["Montant TTC"]
        .sum()
        .reset_index()
    )

    poste_sel = st.selectbox(
        "Poste analysé",
        sorted(evol["Poste"].unique()),
        key="poste_pluri"
    )

    st.line_chart(
        evol[evol["Poste"] == poste_sel]
        .set_index("Année")["Montant TTC"]
    )

# =========================
# MESSAGE COPROPRIÉTAIRE
# =========================
if mode_copro:
    st.markdown("## 📝 Message de synthèse")

    part_top3 = (
        synthese.head(3)["Montant TTC"].sum() / total * 100
    )

    st.success(
        f"Les **3 principaux postes de charges** représentent "
        f"{part_top3:.1f} % des dépenses totales. "
        "Les actions proposées ciblent prioritairement ces postes."
    )

# =========================
# FOOTER
# =========================
st.markdown("---")
st.markdown(
    "*Application de pilotage des charges – Conseil syndical / Copropriété*"
)
