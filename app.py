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
    Analyse des charges à partir d’une **base CSV unique**  
    destinée au **conseil syndical** et aux **copropriétaires**.
    """
)

# =========================
# SESSION STATE
# =========================
if "df_factures" not in st.session_state:
    st.session_state.df_factures = None

# =========================
# MODE COPROPRIÉTAIRE
# =========================
mode_copro = st.toggle(
    "Mode copropriétaire (lecture simplifiée)",
    value=False
)

# =========================
# IMPORT BASE CSV
# =========================
st.markdown("## 📥 Import de la base des dépenses (CSV)")

uploaded_csv = st.file_uploader(
    "Importer la base CSV (depuis Dropbox)",
    type=["csv"]
)

if uploaded_csv:
    try:
        df = pd.read_csv(uploaded_csv, sep=None, engine="python")
        df.columns = [c.strip().replace("\ufeff", "") for c in df.columns]

        # Vérification minimale
        required_cols = [
            "Année", "Compte", "Poste", "Fournisseur",
            "Date", "Montant TTC"
        ]
        missing = [c for c in required_cols if c not in df.columns]
        if missing:
            st.error(f"Colonnes manquantes : {', '.join(missing)}")
        else:
            st.session_state.df_factures = df
            st.success("Base CSV chargée avec succès")

    except Exception as e:
        st.error(f"Erreur de lecture du CSV : {e}")

# =========================
# ARRÊT SI PAS DE DONNÉES
# =========================
if st.session_state.df_factures is None:
    st.info("Veuillez importer une base CSV pour démarrer.")
    st.stop()

df = st.session_state.df_factures

# =========================
# FILTRE ANNÉE
# =========================
annees = sorted(df["Année"].dropna().unique())
annee_sel = st.selectbox("Exercice analysé", annees)

df_annee = df[df["Année"] == annee_sel]

# =========================
# SYNTHÈSE PAR POSTE (COMMUNE)
# =========================
st.markdown("## 📊 Synthèse des charges par poste")

synthese = (
    df_annee.groupby("Poste")["Montant TTC"]
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
    f"des charges totales de l’exercice."
)

# =========================
# GRAPHIQUE SIMPLE (COPRO)
# =========================
st.markdown("### Répartition des charges")
st.bar_chart(
    synthese.set_index("Poste")["Montant TTC"]
)

# =========================
# DÉTAILS CONSEIL SYNDICAL
# =========================
if not mode_copro:
    st.markdown("## 🔍 Analyse détaillée (conseil syndical)")

    # Détail par fournisseur
    st.markdown("### Charges par fournisseur")
    fournisseurs = (
        df_annee.groupby("Fournisseur")["Montant TTC"]
        .sum()
        .reset_index()
        .sort_values("Montant TTC", ascending=False)
    )
    st.dataframe(fournisseurs, use_container_width=True)

    # Fréquence des factures
    st.markdown("### Fréquence des factures")
    freq = (
        df_annee.groupby("Poste")
        .size()
        .reset_index(name="Nombre de factures")
        .sort_values("Nombre de factures", ascending=False)
    )
    st.dataframe(freq, use_container_width=True)

    # Détail brut
    st.markdown("### Détail facture par facture")
    st.dataframe(df_annee, use_container_width=True)

# =========================
# PLURIANNUEL (SI DISPONIBLE)
# =========================
if df["Année"].nunique() >= 2:
    st.markdown("## 📈 Évolution pluriannuelle")

    evol = (
        df.groupby(["Année", "Poste"])["Montant TTC"]
        .sum()
        .reset_index()
    )

    poste_sel = st.selectbox(
        "Poste analysé",
        sorted(evol["Poste"].unique())
    )

    evol_poste = evol[evol["Poste"] == poste_sel]
    st.line_chart(
        evol_poste.set_index("Année")["Montant TTC"]
    )

# =========================
# CONCLUSION PÉDAGOGIQUE (COPRO)
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
# EXPORT CSV FILTRÉ
# =========================
if not mode_copro:
    st.markdown("## 📤 Export")

    export_file = f"depenses_{annee_sel}.csv"
    df_annee.to_csv(export_file, index=False, encoding="utf-8")

    with open(export_file, "rb") as f:
        st.download_button(
            "📥 Télécharger les dépenses de l’année",
            f,
            file_name=export_file,
            mime="text/csv"
        )

# =========================
# FOOTER
# =========================
st.markdown("---")
st.markdown(
    "*Application de pilotage des charges – usage conseil syndical / copropriété*"
)
