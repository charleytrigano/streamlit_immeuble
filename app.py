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
    **Suivi budgétaire à granularité variable (3 ou 4 chiffres)**  
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
        columns=["annee", "compte", "budget"]
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
else:
    df_final = df.copy()

# =========================
# 💰 IMPORT & ÉDITION BUDGET
# =========================
if not mode_copro:
    st.markdown("## 💰 Budget (granularité libre)")

    uploaded_budget = st.file_uploader(
        "Importer le budget (CSV)",
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
                "Budget": "budget"
            })

            df_budget["compte"] = df_budget["compte"].astype(str)

            st.session_state.df_budget = df_budget
            st.success("Budget chargé")

        except Exception as e:
            st.error(f"Erreur budget : {e}")

df_budget = st.session_state.df_budget

# =========================
# 📊 BUDGET vs RÉEL (GRANULARITÉ DYNAMIQUE)
# =========================
if not mode_copro and not df_budget.empty:
    st.markdown("## 📊 Budget vs Réel")

    # Budget de l'année
    budget_annee = df_budget[df_budget["annee"] == annee_sel].copy()

    # Longueur de clé décidée par le budget
    budget_annee["cle_budget"] = budget_annee["compte"]

    # Application de la granularité aux dépenses
    df_reel = df_final[df_final["annee"] == annee_sel].copy()
    df_reel["cle_budget"] = df_reel.apply(
        lambda r: r["Compte"][:len(budget_annee.loc[
            budget_annee["compte"].str.startswith(r["Compte"][:3])
        ]["compte"].iloc[0])]
        if not budget_annee.empty else r["Compte"][:3],
        axis=1
    )

    reel = (
        df_reel.groupby("cle_budget")["montant_ttc"]
        .sum()
        .reset_index()
    )

    comp = reel.merge(
        budget_annee,
        left_on="cle_budget",
        right_on="compte",
        how="left"
    )

    comp["écart (€)"] = comp["montant_ttc"] - comp["budget"]
    comp["écart (%)"] = (comp["écart (€)"] / comp["budget"]) * 100

    st.dataframe(
        comp[["cle_budget", "montant_ttc", "budget", "écart (€)", "écart (%)"]],
        use_container_width=True
    )

# =========================
# FOOTER
# =========================
st.markdown("---")
st.markdown(
    "*Application de pilotage des charges – Conseil syndical / Copropriété*"
)
