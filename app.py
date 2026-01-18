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
from utils.projection import project_baseline, apply_scenario
from utils.graphs_projection import plot_projection
from utils.report_ag import generate_ag_report

# =========================
# CONFIG STREAMLIT
# =========================
st.set_page_config(
    page_title="Pilotage des charges – Immeuble",
    layout="wide"
)

st.title("Pilotage stratégique des charges de l’immeuble")
st.markdown(
    """
    Outil complet d’aide à la décision pour **conseil syndical**, **syndic**
    et **copropriétaires** :
    - analyse facture par facture  
    - budget vs réel  
    - tendances pluriannuelles  
    - projections & scénarios  
    - **rapport AG PDF automatique**
    """
)

# =========================
# SESSION STATE
# =========================
if "historique" not in st.session_state:
    st.session_state.historique = []

# =========================
# SIDEBAR
# =========================
st.sidebar.header("Paramètres")

annee = st.sidebar.number_input(
    "Année analysée",
    value=2025,
    step=1
)

st.sidebar.markdown(
    """
    **Étapes**
    1. Comptes comptables  
    2. Factures PDF  
    3. Analyse annuelle  
    4. Budget voté  
    5. Projection  
    6. Rapport AG PDF  
    """
)

# =========================
# 1️⃣ COMPTES
# =========================
st.markdown("## 1️⃣ Comptes comptables")

comptes_text = st.text_area(
    "Un compte par ligne (noms EXACTS des dossiers)",
    height=150,
    placeholder="Entretien plomberie\nContrat entretien ascenseur\nEau\nAssurances"
)

comptes = [c.strip() for c in comptes_text.splitlines() if c.strip()]

# =========================
# 2️⃣ UPLOAD PDF
# =========================
st.markdown("## 2️⃣ Upload des factures PDF")

structure = {}

if comptes:
    for compte in comptes:
        files = st.file_uploader(
            f"📂 {compte}",
            type="pdf",
            accept_multiple_files=True,
            key=f"{compte}_{annee}"
        )
        if files:
            structure[compte] = files
else:
    st.info("Veuillez saisir au moins un compte comptable.")

# =========================
# 3️⃣ ANALYSE ANNUELLE
# =========================
st.markdown("## 3️⃣ Analyse annuelle")

df = None
synthese = None

if st.button("🚀 Lancer l’analyse annuelle"):
    if not structure:
        st.warning("Aucune facture PDF fournie.")
    else:
        with st.spinner("Analyse des factures en cours..."):
            df = analyse_pdfs(structure, annee)

        st.session_state.historique.append(df)
        st.success(f"Analyse {annee} terminée")

        st.markdown("### 📄 Factures")
        st.dataframe(df, use_container_width=True)

        st.markdown("### 📊 Synthèse par poste")
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

        st.markdown("### 📈 Analyses graphiques")
        plot_charges_par_poste(df)
        plot_pareto_postes(df)
        plot_top_fournisseurs(df)
        plot_recurrent_vs_ponctuel(df)

# =========================
# 4️⃣ BUDGET VS RÉEL
# =========================
st.markdown("## 4️⃣ Budget voté vs Réel")

df_bvr = None

budget_file = st.file_uploader(
    "Uploader le budget voté (Excel)",
    type=["xlsx"]
)

if budget_file and st.session_state.historique:
    try:
        df_budget = load_budget(budget_file)
        df_latest = st.session_state.historique[-1]
        df_bvr = analyse_budget_vs_reel(df_latest, df_budget)

        st.dataframe(df_bvr, use_container_width=True)
        plot_budget_vs_reel(df_bvr)

    except Exception as e:
        st.error(str(e))

# =========================
# 5️⃣ PLURIANNUEL
# =========================
st.markdown("## 5️⃣ Analyse pluriannuelle")

df_pluri = None
df_trends = None

if len(st.session_state.historique) >= 2:
    df_pluri = aggregate_pluriannuel(st.session_state.historique)
    df_trends = compute_trends(df_pluri)

    st.dataframe(df_trends, use_container_width=True)
    plot_global_trends(df_pluri)

    poste_sel = st.selectbox(
        "Évolution par poste",
        sorted(df_pluri["Poste"].unique())
    )
    plot_trend_par_poste(df_pluri, poste_sel)
else:
    st.info("Analysez au moins deux années pour activer le pluriannuel.")

# =========================
# 6️⃣ V5 – PROJECTION
# =========================
st.markdown("## 6️⃣ Projection & scénarios")

df_proj_all = None
economie = None

if df_trends is not None:
    annee_ref = int(df_trends["Année"].max())
    df_proj_base = project_baseline(df_trends, annee_ref)

    st.markdown("### 🎯 Scénario d’économies")
    reductions = {}

    for poste in sorted(df_proj_base["Poste"].unique()):
        taux = st.slider(
            f"{poste} – réduction (%)",
            0, 40, 0, 5
        )
        if taux > 0:
            reductions[poste] = taux

    df_proj_scen = apply_scenario(df_proj_base, reductions)
    df_proj_all = pd.concat([df_proj_base, df_proj_scen])

    plot_projection(df_proj_all)

    economie = (
        df_proj_base.groupby("Année")["Montant_Projeté"].sum()
        - df_proj_scen.groupby("Année")["Montant_Projeté"].sum()
    ).sum()

    st.success(f"💡 Économie cumulée estimée : {economie:,.0f} €")

# =========================
# 7️⃣ V6 – RAPPORT AG PDF
# =========================
st.markdown("## 7️⃣ Rapport AG (PDF)")

if st.session_state.historique:
    if st.button("📄 Générer le rapport AG (PDF)"):
        df_latest = st.session_state.historique[-1]

        synthese_poste = (
            df_latest.groupby("Poste")
            .agg(
                Montant_Total=("Montant TTC", "sum"),
                Nb_Factures=("Fichier", "count"),
                Nb_Fournisseurs=("Fournisseur", "nunique")
            )
            .reset_index()
            .sort_values("Montant_Total", ascending=False)
        )

        pdf_path = f"rapport_AG_{annee}.pdf"

        generate_ag_report(
            filepath=pdf_path,
            annee=annee,
            synthese_poste=synthese_poste,
            budget_vs_reel=df_bvr,
            pluriannuel=df_trends,
            projection=df_proj_all,
            economie=economie
        )

        with open(pdf_path, "rb") as f:
            st.download_button(
                "📥 Télécharger le rapport AG (PDF)",
                f,
                file_name=pdf_path,
                mime="application/pdf"
            )

# =========================
# FOOTER
# =========================
st.markdown("---")
st.markdown(
    "*Outil de pilotage des charges – Conseil syndical / Syndic / Copropriété*"
)
