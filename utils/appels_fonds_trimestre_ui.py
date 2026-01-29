import streamlit as st
import pandas as pd

# =========================
# UTILS
# =========================
def euro(x):
    return f"{x:,.2f} €".replace(",", " ").replace(".", ",")

# =========================
# MAPPING GROUPES → TANTIÈMES
# =========================
TANTIEMES_MAP = {
    1: "tantiemes",
    2: "tantiemes_rdc_sous_sols",
    3: "tantiemes_sous_sols",
    4: "tantiemes_ascenseur",
    5: "tantiemes_monte_voiture",
}

GROUPES_LABELS = {
    1: "Charges communes générales",
    2: "Charges spéciales RDC / sous-sols",
    3: "Charges spéciales sous-sols",
    4: "Ascenseurs",
    5: "Monte-voiture",
}

# =========================
# UI
# =========================
def appels_fonds_trimestre_ui(supabase, annee):
    st.header("📢 Appels de fonds trimestriels")

    trimestre = st.selectbox(
        "Trimestre",
        ["T1", "T2", "T3", "T4"],
        index=0
    )

    # =========================
    # LOAD DATA
    # =========================
    df_bud = pd.DataFrame(
        supabase.table("budgets")
        .select("*")
        .eq("annee", annee)
        .execute()
        .data
    )

    df_plan = pd.DataFrame(
        supabase.table("plan_comptable")
        .select("groupe_compte, groupe_charges")
        .execute()
        .data
    )

    df_lots = pd.DataFrame(
        supabase.table("lots")
        .select("*")
        .execute()
        .data
    )

    if df_bud.empty or df_lots.empty:
        st.warning("Aucun budget ou aucun lot.")
        return

    # =========================
    # BUDGET PAR GROUPE DE CHARGES
    # =========================
    df_bud = df_bud.merge(
        df_plan,
        on="groupe_compte",
        how="left"
    )

    df_budget_groupes = (
        df_bud
        .groupby("groupe_charges", as_index=False)
        .agg(budget_annuel=("budget", "sum"))
    )

    df_budget_groupes["budget_trimestre"] = df_budget_groupes["budget_annuel"] / 4

    # =========================
    # RÉPARTITION PAR LOT
    # =========================
    lignes = []

    for _, row in df_budget_groupes.iterrows():
        groupe = int(row["groupe_charges"])
        col_tantiemes = TANTIEMES_MAP.get(groupe)

        if col_tantiemes not in df_lots.columns:
            continue

        total_tantiemes = df_lots[col_tantiemes].fillna(0).sum()
        if total_tantiemes == 0:
            continue

        for _, lot in df_lots.iterrows():
            part = lot[col_tantiemes] or 0
            montant = row["budget_trimestre"] * part / total_tantiemes

            lignes.append({
                "lot_id": lot["lot_id"],
                "lot": lot.get("lot"),
                "groupe_charges": GROUPES_LABELS.get(groupe, f"Groupe {groupe}"),
                "appel_trimestriel": montant
            })

    df_appels = pd.DataFrame(lignes)

    # =========================
    # TOTAL PAR LOT
    # =========================
    df_total_lot = (
        df_appels
        .groupby(["lot_id", "lot"], as_index=False)
        .agg(total_trimestre=("appel_trimestriel", "sum"))
    )

    # =========================
    # LOI ALUR (5 %)
    # =========================
    budget_annuel_total = df_budget_groupes["budget_annuel"].sum()
    alur_trimestre = budget_annuel_total / 4 * 0.05

    total_tantiemes_gen = df_lots["tantiemes"].fillna(0).sum()

    alur_lignes = []
    for _, lot in df_lots.iterrows():
        part = lot["tantiemes"] or 0
        montant = alur_trimestre * part / total_tantiemes_gen if total_tantiemes_gen else 0

        alur_lignes.append({
            "lot_id": lot["lot_id"],
            "lot": lot.get("lot"),
            "Loi ALUR": montant
        })

    df_alur = pd.DataFrame(alur_lignes)

    # =========================
    # AFFICHAGE
    # =========================
    st.subheader("📋 Détail par groupe de charges")
    st.dataframe(
        df_appels.assign(appel_trimestriel=df_appels["appel_trimestriel"].apply(euro)),
        use_container_width=True
    )

    st.subheader("📊 Total par lot")
    st.dataframe(
        df_total_lot.assign(total_trimestre=df_total_lot["total_trimestre"].apply(euro)),
        use_container_width=True
    )

    st.subheader("⚖️ Ligne Loi ALUR (5 %)")
    st.dataframe(
        df_alur.assign(**{"Loi ALUR": df_alur["Loi ALUR"].apply(euro)}),
        use_container_width=True
    )