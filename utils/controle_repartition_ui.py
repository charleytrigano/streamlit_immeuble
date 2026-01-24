import streamlit as st
import pandas as pd

TOLERANCE = 0.01  # tolérance arrondi

def controle_repartition_ui(supabase):
    st.title("✅ Contrôle de répartition des dépenses")

    # -------------------------
    # Sélection année
    # -------------------------
    annee = st.selectbox(
        "Année",
        [2023, 2024, 2025, 2026],
        index=0
    )

    # -------------------------
    # Chargement dépenses
    # -------------------------
    dep_resp = (
        supabase
        .table("depenses")
        .select("id, montant_ttc")
        .eq("annee", annee)
        .execute()
    )

    if not dep_resp.data:
        st.warning("Aucune dépense pour cette année.")
        return

    df_dep = pd.DataFrame(dep_resp.data)

    # -------------------------
    # Chargement répartitions
    # -------------------------
    rep_resp = (
        supabase
        .table("repartition_depenses")
        .select("depense_id, montant_reparti")
        .execute()
    )

    df_rep = pd.DataFrame(rep_resp.data) if rep_resp.data else pd.DataFrame(
        columns=["depense_id", "montant_reparti"]
    )

    # -------------------------
    # Agrégation
    # -------------------------
    df_rep_sum = (
        df_rep
        .groupby("depense_id", as_index=False)
        .agg(montant_reparti=("montant_reparti", "sum"))
    )

    df = df_dep.merge(
        df_rep_sum,
        left_on="id",
        right_on="depense_id",
        how="left"
    ).fillna(0)

    df["ecart"] = df["montant_ttc"] - df["montant_reparti"]

    # -------------------------
    # KPI globaux
    # -------------------------
    total_depenses = df["montant_ttc"].sum()
    total_reparti = df["montant_reparti"].sum()
    ecart_global = total_depenses - total_reparti

    col1, col2, col3 = st.columns(3)

    col1.metric("Total dépenses (€)", f"{total_depenses:,.2f}")
    col2.metric("Total réparti (€)", f"{total_reparti:,.2f}")
    col3.metric(
        "Écart global (€)",
        f"{ecart_global:,.2f}",
        delta=None if abs(ecart_global) <= TOLERANCE else "⚠️"
    )

    # -------------------------
    # Résultat du contrôle
    # -------------------------
    st.markdown("### 📋 Détail des anomalies")

    anomalies = df[abs(df["ecart"]) > TOLERANCE]

    if anomalies.empty:
        st.success("✅ Toutes les dépenses sont correctement réparties.")
    else:
        st.error(f"❌ {len(anomalies)} dépense(s) non ou mal répartie(s).")

        st.dataframe(
            anomalies.rename(columns={
                "montant_ttc": "Montant dépense (€)",
                "montant_reparti": "Montant réparti (€)",
                "ecart": "Écart (€)"
            })[[
                "id",
                "Montant dépense (€)",
                "Montant réparti (€)",
                "Écart (€)"
            ]],
            use_container_width=True
        )
