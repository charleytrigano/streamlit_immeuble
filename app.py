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
        columns=["annee", "compte", "compte_general", "budget"]
    )

# =========================
# MODE COPROPRIÉTAIRE
# =========================
mode_copro = st.toggle(
    "Mode copropriétaire (lecture simplifiée)",
    value=False
)

# =========================
# IMPORT DÉPENSES
# =========================
st.markdown("## 📥 Import des dépenses (CSV)")

uploaded_csv = st.file_uploader(
    "Importer la base des dépenses",
    type=["csv"]
)

if uploaded_csv:
    try:
        df = pd.read_csv(uploaded_csv, sep=None, engine="python")

        # Nettoyage colonnes
        df.columns = [c.strip().replace("\ufeff", "") for c in df.columns]

        required = [
            "Année", "Compte", "Poste",
            "Fournisseur", "Date", "Montant TTC"
        ]
        missing = [c for c in required if c not in df.columns]

        if missing:
            st.error(f"Colonnes manquantes : {', '.join(missing)}")
        else:
            df["Compte"] = df["Compte"].astype(str)
            df["compte_general"] = df["Compte"].str[:2]

            # Normalisation noms
            df = df.rename(columns={
                "Année": "annee",
                "Montant TTC": "montant_ttc"
            })

            st.session_state.df_factures = df
            st.success("Dépenses chargées avec succès")

    except Exception as e:
        st.error(f"Erreur de lecture du CSV : {e}")

# =========================
# STOP SI PAS DE DONNÉES
# =========================
if st.session_state.df_factures is None:
    st.info("Veuillez importer un fichier de dépenses.")
    st.stop()

df = st.session_state.df_factures

# =========================
# FILTRE ANNÉE
# =========================
annees = sorted(df["annee"].unique())
annee_sel = st.selectbox("Exercice analysé", annees)

df_annee = df[df["annee"] == annee_sel]

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

    df_autres = df[df["annee"] != annee_sel]
    df_final = pd.concat([df_autres, df_edit], ignore_index=True)

    export_file = f"depenses_corrigees_{annee_sel}.csv"
    df_final.to_csv(export_file, index=False, encoding="utf-8")

    with open(export_file, "rb") as f:
        st.download_button(
            "📥 Télécharger les dépenses mises à jour",
            f,
            file_name=export_file
        )
else:
    df_final = df.copy()

# =========================
# SYNTHÈSE PAR POSTE
# =========================
st.markdown("## 📊 Synthèse par poste")

synth_poste = (
    df_final[df_final["annee"] == annee_sel]
    .groupby("Poste")["montant_ttc"]
    .sum()
    .reset_index()
    .sort_values("montant_ttc", ascending=False)
)

st.dataframe(synth_poste, use_container_width=True)

# =========================
# 💰 IMPORT & ÉDITION BUDGET
# =========================
if not mode_copro:
    st.markdown("## 💰 Budget par comptes généraux")

    uploaded_budget = st.file_uploader(
        "Importer le budget",
        type=["csv"],
        key="budget"
    )

    if uploaded_budget:
        try:
            df_budget = pd.read_csv(uploaded_budget, sep=None, engine="python")
            df_budget.columns = [c.strip().replace("\ufeff", "") for c in df_budget.columns]

            df_budget = df_budget.rename(columns={
                "Année": "annee",
                "Compte": "compte",
                "Comptes généraux": "compte_general",
                "Budget": "budget"
            })

            st.session_state.df_budget = df_budget
            st.success("Budget chargé")

        except Exception as e:
            st.error(f"Erreur budget : {e}")

    df_budget = st.session_state.df_budget
    df_budget_annee = df_budget[df_budget["annee"] == annee_sel]

    df_budget_edit = st.data_editor(
        df_budget_annee,
        num_rows="dynamic",
        use_container_width=True
    )

    df_budget_autres = df_budget[df_budget["annee"] != annee_sel]
    df_budget_final = pd.concat(
        [df_budget_autres, df_budget_edit],
        ignore_index=True
    )

    st.session_state.df_budget = df_budget_final

# =========================
# 📊 BUDGET vs RÉEL (FIX)
# =========================
if not mode_copro and not st.session_state.df_budget.empty:
    st.markdown("## 📊 Budget vs Réel (comptes généraux)")

    reel = (
        df_final[df_final["annee"] == annee_sel]
        .groupby("compte_general")["montant_ttc"]
        .sum()
        .reset_index()
    )

    budget = st.session_state.df_budget
    budget_annee = budget[budget["annee"] == annee_sel]

    comp = reel.merge(
        budget_annee,
        on="compte_general",
        how="left"
    )

    comp["écart (€)"] = comp["montant_ttc"] - comp["budget"]
    comp["écart (%)"] = (comp["écart (€)"] / comp["budget"]) * 100

    st.dataframe(comp, use_container_width=True)

# =========================
# FOOTER
# =========================
st.markdown("---")
st.markdown(
    "*Application de pilotage des charges – Conseil syndical / Copropriété*"
)
