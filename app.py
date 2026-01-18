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
    Pilotage budgétaire et analyse des charges  
    **Budget suivi par comptes généraux (2 chiffres)**  
    Source unique : **CSV**
    """
)

# =========================
# SESSION STATE
# =========================
if "df_factures" not in st.session_state:
    st.session_state.df_factures = None

if "df_budget" not in st.session_state:
    st.session_state.df_budget = pd.DataFrame(
        columns=["Année", "Compte", "Comptes généraux", "Budget"]
    )

# =========================
# MODE COPROPRIÉTAIRE
# =========================
mode_copro = st.toggle(
    "Mode copropriétaire (lecture simplifiée)",
    value=False
)

# =========================
# IMPORT DÉPENSES (CSV)
# =========================
st.markdown("## 📥 Import des dépenses")

uploaded_csv = st.file_uploader(
    "Importer la base des dépenses (CSV)",
    type=["csv"]
)

if uploaded_csv:
    try:
        df = pd.read_csv(uploaded_csv, sep=None, engine="python")
        df.columns = [c.strip().replace("\ufeff", "") for c in df.columns]

        required = [
            "Année", "Compte", "Poste",
            "Fournisseur", "Date", "Montant TTC"
        ]
        missing = [c for c in required if c not in df.columns]

        if missing:
            st.error(f"Colonnes manquantes : {', '.join(missing)}")
        else:
            # Ajout du compte général (2 premiers chiffres)
            df["Compte"] = df["Compte"].astype(str)
            df["Comptes généraux"] = df["Compte"].str[:2]

            st.session_state.df_factures = df
            st.success("Dépenses chargées avec succès")

    except Exception as e:
        st.error(f"Erreur de lecture du CSV : {e}")

# =========================
# STOP SI PAS DE DONNÉES
# =========================
if st.session_state.df_factures is None:
    st.info("Veuillez importer un fichier de dépenses pour continuer.")
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

    df_edit = st.data_editor(
        df_annee,
        num_rows="dynamic",
        use_container_width=True
    )

    df_autres = df[df["Année"] != annee_sel]
    df_final = pd.concat([df_autres, df_edit], ignore_index=True)

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
# 📊 SYNTHÈSE PAR POSTE (INFO)
# =========================
st.markdown("## 📊 Synthèse par poste")

synth_poste = (
    df_final[df_final["Année"] == annee_sel]
    .groupby("Poste")["Montant TTC"]
    .sum()
    .reset_index()
    .sort_values("Montant TTC", ascending=False)
)

st.dataframe(synth_poste, use_container_width=True)
st.bar_chart(synth_poste.set_index("Poste")["Montant TTC"])

# =========================
# 💰 BUDGET – COMPTES GÉNÉRAUX
# =========================
if not mode_copro:
    st.markdown("## 💰 Budget par comptes généraux")

    uploaded_budget = st.file_uploader(
        "Importer le budget (CSV)",
        type=["csv"],
        key="budget_upload"
    )

    if uploaded_budget:
        try:
            df_budget = pd.read_csv(uploaded_budget, sep=None, engine="python")
            df_budget.columns = [c.strip() for c in df_budget.columns]
            st.session_state.df_budget = df_budget
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

    budget_file = f"budget_comptes_generaux_{annee_sel}.csv"
    df_budget_final.to_csv(budget_file, index=False, encoding="utf-8")

    with open(budget_file, "rb") as f:
        st.download_button(
            "📥 Télécharger le budget mis à jour",
            f,
            file_name=budget_file,
            mime="text/csv"
        )

# =========================
# 📊 BUDGET vs RÉEL (COMPTES GÉNÉRAUX)
# =========================
if not mode_copro and not st.session_state.df_budget.empty:
    st.markdown("## 📊 Budget vs Réel (comptes généraux)")

    reel = (
        df_final[df_final["Année"] == annee_sel]
        .groupby("Comptes généraux")["Montant TTC"]
        .sum()
        .reset_index()
    )

    budget = st.session_state.df_budget
    budget_annee = budget[budget["Année"] == annee_sel]

    comp = reel.merge(
        budget_annee,
        on="Comptes généraux",
        how="left"
    )

    comp["Écart (€)"] = comp["Montant TTC"] - comp["Budget"]
    comp["Écart (%)"] = (comp["Écart (€)"] / comp["Budget"]) * 100

    st.dataframe(comp, use_container_width=True)

# =========================
# 📈 PLURIANNUEL (COMPTES GÉNÉRAUX)
# =========================
if df_final["Année"].nunique() >= 2:
    st.markdown("## 📈 Évolution pluriannuelle (comptes généraux)")

    evol = (
        df_final.groupby(["Année", "Comptes généraux"])["Montant TTC"]
        .sum()
        .reset_index()
    )

    cg_sel = st.selectbox(
        "Compte général",
        sorted(evol["Comptes généraux"].unique())
    )

    st.line_chart(
        evol[evol["Comptes généraux"] == cg_sel]
        .set_index("Année")["Montant TTC"]
    )

# =========================
# MESSAGE COPROPRIÉTAIRE
# =========================
if mode_copro:
    total = synth_poste["Montant TTC"].sum()
    top3 = synth_poste.head(3)["Montant TTC"].sum()

    st.success(
        f"Les **3 principaux postes** représentent "
        f"{top3 / total * 100:.1f} % des charges totales. "
        "Le suivi budgétaire est effectué par grandes catégories comptables."
    )

# =========================
# FOOTER
# =========================
st.markdown("---")
st.markdown(
    "*Application de pilotage des charges – Conseil syndical / Copropriété*"
)
