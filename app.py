import streamlit as st
import pandas as pd

# =========================
# IMPORTS MÉTIERS
# =========================
from utils.analyse import analyse_pdfs
from utils.graphs import (
    plot_charges_par_poste,
    plot_pareto_postes,
    plot_top_fournisseurs,
    plot_recurrent_vs_ponctuel
)
from utils.budget import load_budget
from utils.budget_analysis import analyse_budget_vs_reel
from utils.graphs_budget import plot_budget_vs_reel
from utils.pluriannuel import aggregate_pluriannuel, compute_trends
from utils.graphs_pluri import plot_trend_par_poste, plot_global_trends

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
    Outil d’analyse **facture par facture**, **budget vs réel** et **pluriannuel**  
    à destination du **conseil syndical**, du **syndic** et des **copropriétaires**.
    """
)

# =========================
# SESSION STATE (V4)
# =========================
if "historique" not in st.session_state:
    st.session_state.historique = []

# =========================
# SIDEBAR PARAMÈTRES
# =========================
st.sidebar.header("Paramètres généraux")

annee = st.sidebar.number_input(
    "Année analysée",
    value=2025,
    step=1
)

st.sidebar.markdown("---")
st.sidebar.markdown(
    """
    **Processus**
    1. Saisir les comptes  
    2. Uploader les PDF  
    3. Lancer l’analyse  
    4. Ajouter le budget  
    5. Comparer les années  
    """
)

# =========================
# 1️⃣ COMPTES COMPTABLES
# =========================
st.markdown("## 1️⃣ Comptes comptables")

comptes_text = st.text_area(
    "Liste des comptes (1 par ligne – noms EXACTS des dossiers)",
    height=150,
    placeholder="Entretien plomberie\nContrat entretien ascenseur\nEau\nAssurances"
)

comptes = [c.strip() for c in comptes_text.splitlines() if c.strip()]

# =========================
# 2️⃣ UPLOAD FACTURES
# =========================
st.markdown("## 2️⃣ Upload des factures PDF")

structure = {}

if comptes:
    for compte in comptes:
        fichiers = st.file_uploader(
            f"📂 {compte}",
            type="pdf",
            accept_multiple_files=True,
            key=f"pdf_{compte}_{annee}"
        )
        if fichiers:
            structure[compte] = fichiers
else:
    st.info("Veuillez saisir au moins un compte comptable.")

# =========================
# 3️⃣ ANALYSE ANNUELLE
# =========================
st.markdown("## 3️⃣ Analyse annuelle")

if st.button("🚀 Lancer l’analyse annuelle"):
    if not structure:
        st.warning("Aucune facture PDF n’a été uploadée.")
    else:
        with st.spinner("Analyse des factures en cours…"):
            df = analyse_pdfs(structure, annee)

        st.session_state.historique.append(df)

        st.success(f"Analyse {annee} terminée")

        # -------------------------
        # TABLE FACTURES
        # -------------------------
        st.markdown("## 📄 Détail des factures")
        st.dataframe(df, use_container_width=True)

        # -------------------------
        # SYNTHÈSE PAR POSTE
        # -------------------------
        st.markdown("## 📊 Synthèse par poste")

        synthese = (
            df.groupby(["Compte", "Poste"])
            .agg(
                Montant_Total=("Montant TTC", "sum"),
                Nb_Factures=("Fichier", "count"),
                Nb_Fournisseurs=("Fournisseur", "nunique")
            )
            .reset_index()
            .sort_values("Montant_Total", ascending=False)
        )

        st.dataframe(synthese, use_container_width=True)

        # -------------------------
        # FILTRES
        # -------------------------
        st.markdown("## 🔍 Filtres")

        col1, col2 = st.columns(2)

        with col1:
            filtre_postes = st.multiselect(
                "Filtrer par poste",
                sorted(df["Poste"].unique())
            )

        with col2:
            filtre_fournisseurs = st.multiselect(
                "Filtrer par fournisseur",
                sorted(df["Fournisseur"].unique())
            )

        df_filtre = df.copy()

        if filtre_postes:
            df_filtre = df_filtre[df_filtre["Poste"].isin(filtre_postes)]

        if filtre_fournisseurs:
            df_filtre = df_filtre[df_filtre["Fournisseur"].isin(filtre_fournisseurs)]

        # -------------------------
        # GRAPHIQUES (V2)
        # -------------------------
        st.markdown("## 📈 Analyses graphiques")

        plot_charges_par_poste(df_filtre)
        plot_pareto_postes(df_filtre)
        plot_top_fournisseurs(df_filtre)
        plot_recurrent_vs_ponctuel(df_filtre)

        # -------------------------
        # EXPORT EXCEL
        # -------------------------
        st.markdown("## 📥 Export annuel")

        output = f"analyse_charges_{annee}.xlsx"

        with pd.ExcelWriter(output, engine="openpyxl") as writer:
            df.to_excel(writer, sheet_name="Factures", index=False)
            synthese.to_excel(writer, sheet_name="Synthese_par_poste", index=False)

        with open(output, "rb") as f:
            st.download_button(
                "📥 Télécharger l’analyse Excel",
                f,
                file_name=output,
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )

# =========================
# 4️⃣ BUDGET VS RÉEL (V3)
# =========================
st.markdown("## 💰 Budget voté vs Réel")

budget_file = st.file_uploader(
    "Uploader le fichier Excel du budget voté",
    type=["xlsx"]
)

if budget_file and st.session_state.historique:
    try:
        df_budget = load_budget(budget_file)
        df_latest = st.session_state.historique[-1]

        df_budget_vs_reel = analyse_budget_vs_reel(df_latest, df_budget)

        st.dataframe(df_budget_vs_reel, use_container_width=True)

        plot_budget_vs_reel(df_budget_vs_reel)

        st.markdown("### 📝 Commentaires automatiques (AG)")

        for _, row in df_budget_vs_reel.iterrows():
            if row["Statut"] == "❌ Dépassement":
                st.warning(
                    f"Le poste **{row['Poste']}** dépasse le budget de "
                    f"{row['Écart €']:.0f} € ({row['Écart %']:.1f} %)."
                )

    except Exception as e:
        st.error(str(e))

# =========================
# 5️⃣ ANALYSE PLURIANNUELLE (V4)
# =========================
st.markdown("## 📆 Analyse pluriannuelle")

if len(st.session_state.historique) < 2:
    st.info("Analysez au moins deux années pour activer la vue pluriannuelle.")
else:
    df_pluri = aggregate_pluriannuel(st.session_state.historique)
    df_trends = compute_trends(df_pluri)

    st.markdown("### 🔎 Synthèse pluriannuelle")
    st.dataframe(df_trends, use_container_width=True)

    plot_global_trends(df_pluri)

    poste_sel = st.selectbox(
        "Évolution d’un poste",
        sorted(df_pluri["Poste"].unique())
    )

    plot_trend_par_poste(df_pluri, poste_sel)

    st.markdown("### 🚨 Alertes dérives")

    alertes = df_trends[
        (df_trends["Variation %"] > 10) &
        (~df_trends["Variation %"].isna())
    ]

    if alertes.empty:
        st.success("Aucune dérive significative détectée.")
    else:
        for _, row in alertes.iterrows():
            st.warning(
                f"Le poste **{row['Poste']}** augmente de "
                f"{row['Variation %']:.1f} % en {int(row['Année'])}."
            )

# =========================
# FOOTER
# =========================
st.markdown("---")
st.markdown(
    "*Outil de pilotage des charges – usage conseil syndical / syndic / copropriété*"
)
