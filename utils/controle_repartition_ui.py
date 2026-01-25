import streamlit as st
import pandas as pd

TOLERANCE = 0.01  # tolérance d'arrondi


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
    df_dep["montant_ttc"] = df_dep["montant_ttc"].astype(float)

    # -------------------------
    # Chargement répartitions (quote-part)
    # -------------------------
    rep_resp = (
        supabase
        .table("repartition_depenses")
        .select("depense_id, quote_part")
        .execute()
    )

    if not rep_resp.data:
        st.warning("Aucune répartition enregistrée.")
        return

    df_rep = pd.DataFrame(rep_resp.data)
    df_rep["quote_part"] = df_rep["quote_part"].astype(float)

    # -------------------------
    # Calcul du montant réparti
    # -------------------------
    df = df_rep.merge(
        df_dep,
        left_on="depense_id",
        right_on="id",
        how="left"
    )

    df["montant_reparti"] = df["montant_ttc"] * df["quote_part"]

    # -------------------------
    # Agrégation par dépense
    # -------------------------
    df_sum = (
        df
        .groupby("depense_id", as_index=False)
        .agg(
            montant_ttc=("montant_ttc", "first"),
            montant_reparti=("montant_reparti", "sum")
        )
    )

    df_sum["ecart"] = df_sum["montant_ttc"] - df_sum["montant_reparti"]

    # ==========================================================
    # ✅ AMÉLIORATION 1 : détecter les dépenses sans répartition
    # ==========================================================
    depenses_non_reparties = df_dep[
        ~df_dep["id"].isin(df_sum["depense_id"])
    ].copy()

    if not depenses_non_reparties.empty:
        depenses_non_reparties["montant_reparti"] = 0.0
        depenses_non_reparties["ecart"] = depenses_non_reparties["montant_ttc"]
        depenses_non_reparties = depenses_non_reparties.rename(
            columns={"id": "depense_id"}
        )

        df_sum = pd.concat(
            [
                df_sum,
                depenses_non_reparties[[
                    "depense_id",
                    "montant_ttc",
                    "montant_reparti",
                    "ecart"
                ]]
            ],
            ignore_index=True
        )

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
    # Anomalies
    # -------------------------
    st.markdown("### 📋 Dépenses mal réparties")

    anomalies = df_sum[abs(df_sum["ecart"]) > TOLERANCE]

    if anomalies.empty:
        st.success("✅ Toutes les dépenses sont correctement réparties.")
    else:
        st.error(f"❌ {len(anomalies)} dépense(s) incorrectement répartie(s).")

        st.dataframe(
            anomalies.rename(columns={
                "depense_id": "ID dépense",
                "montant_ttc": "Montant dépense (€)",
                "montant_reparti": "Montant réparti (€)",
                "ecart": "Écart (€)"
            }).sort_values("Écart (€)", ascending=False),
            use_container_width=True
        )