import streamlit as st
import pandas as pd

TOLERANCE = 0.01      # tolérance d'arrondi en euros
BASE_REPARTITION = 10000  # quote-part exprimée en 1 / 10 000


def controle_repartition_ui(supabase):
    st.title("✅ Contrôle de répartition des dépenses")

    # -------------------------
    # Sélection année
    # -------------------------
    annee = st.selectbox("Année", [2023, 2024, 2025, 2026], index=0)

    # -------------------------
    # Chargement DÉPENSES
    # -------------------------
    dep_resp = (
        supabase
        .table("depenses")
        .select("id, montant_ttc, compte")
        .eq("annee", annee)
        .execute()
    )

    if not dep_resp.data:
        st.warning("Aucune dépense pour cette année.")
        return

    df_dep = pd.DataFrame(dep_resp.data)

    # -------------------------
    # Chargement RÉPARTITIONS
    # -------------------------
    rep_resp = (
        supabase
        .table("repartition_depenses")
        .select("depense_id, lot_id, quote_part")
        .execute()
    )

    if not rep_resp.data:
        st.warning("Aucune répartition enregistrée.")
        return

    df_rep = pd.DataFrame(rep_resp.data)

    # -------------------------
    # Jointure + normalisation (A)
    # -------------------------
    df = df_rep.merge(
        df_dep,
        left_on="depense_id",
        right_on="id",
        how="left"
    )

    # quote_part est en 1 / 10 000
    df["quote_norm"] = df["quote_part"] / BASE_REPARTITION
    df["montant_reparti"] = df["montant_ttc"] * df["quote_norm"]

    # -------------------------
    # Agrégation par dépense (on garde le compte) (B)
    # -------------------------
    df_sum = (
        df
        .groupby(["depense_id", "compte"], as_index=False)
        .agg(
            montant_ttc=("montant_ttc", "first"),
            montant_reparti=("montant_reparti", "sum")
        )
    )

    df_sum["ecart"] = df_sum["montant_ttc"] - df_sum["montant_reparti"]

    # -------------------------
    # KPI globaux
    # -------------------------
    total_depenses = df_sum["montant_ttc"].sum()
    total_reparti = df_sum["montant_reparti"].sum()
    ecart_global = total_depenses - total_reparti

    col1, col2, col3 = st.columns(3)
    col1.metric("Total dépenses (€)", f"{total_depenses:,.2f}")
    col2.metric("Total réparti (€)", f"{total_reparti:,.2f}")
    col3.metric("Écart global (€)", f"{ecart_global:,.2f}")

    # -------------------------
    # Dépenses en anomalie
    # -------------------------
    st.markdown("### ❌ Dépenses mal réparties")

    anomalies = df_sum[abs(df_sum["ecart"]) > TOLERANCE]

    if anomalies.empty:
        st.success("✅ Toutes les dépenses sont correctement réparties.")
        return

    st.error(f"{len(anomalies)} dépense(s) incorrectement répartie(s).")

    # on fixe l'ordre des colonnes pour bien voir le compte
    anomalies_view = anomalies[[
        "depense_id",
        "compte",
        "montant_ttc",
        "montant_reparti",
        "ecart",
    ]].rename(columns={
        "depense_id": "ID dépense",
        "compte": "Compte",
        "montant_ttc": "Montant dépense (€)",
        "montant_reparti": "Montant réparti (€)",
        "ecart": "Écart (€)",
    })

    st.dataframe(anomalies_view, use_container_width=True)

    # -------------------------
    # Détail par lot pour les seules anomalies (C)
    # -------------------------
    st.markdown("### 🔎 Détail par lot des dépenses en anomalie")

    detail = df.merge(
        anomalies[["depense_id"]],
        on="depense_id",
        how="inner"
    )

    detail_view = detail[[
        "depense_id",
        "compte",
        "lot_id",
        "quote_part",
        "montant_reparti",
    ]].rename(columns={
        "depense_id": "ID dépense",
        "compte": "Compte",
        "lot_id": "Lot",
        "quote_part": "Quote-part (‰)",
        "montant_reparti": "Montant réparti (€)",
    })

    st.dataframe(detail_view, use_container_width=True)