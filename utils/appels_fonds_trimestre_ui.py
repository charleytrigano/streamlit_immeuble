import streamlit as st
import pandas as pd

GROUPES_CHARGES = {
    1: "Charges communes générales",
    2: "Charges spéciales RDC / sous-sol",
    3: "Charges spéciales sous-sol",
    4: "Charges garages / parkings",
    5: "Ascenseurs",
    6: "Monte-voitures",
}

def euro(x):
    return f"{x:,.2f} €".replace(",", " ").replace(".", ",")

def appels_fonds_trimestre_ui(supabase, annee):
    st.subheader(f"📢 Appels de fonds trimestriels – {annee}")

    # =========================
    # CHARGEMENT DES DONNÉES
    # =========================
    df_budget = pd.DataFrame(
        supabase.table("budgets")
        .select("groupe_compte, budget")
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
        .select("lot_id, proprietaire, tantiemes")
        .execute()
        .data
    )

    if df_budget.empty or df_plan.empty or df_lots.empty:
        st.warning("Données insuffisantes pour calculer les appels de fonds")
        return

    # =========================
    # BUDGET PAR GROUPE DE CHARGES
    # =========================
    df_budget = df_budget.merge(
        df_plan, on="groupe_compte", how="left"
    )

    df_budget_grp = (
        df_budget
        .groupby("groupe_charges", as_index=False)["budget"]
        .sum()
    )

    # =========================
    # RÉPARTITION PAR LOT
    # =========================
    total_tantiemes = df_lots["tantiemes"].sum()

    repartitions = []

    for _, lot in df_lots.iterrows():
        for _, row in df_budget_grp.iterrows():
            part = (
                row["budget"]
                * lot["tantiemes"]
                / total_tantiemes
            )

            repartitions.append({
                "proprietaire": lot["proprietaire"],
                "groupe_charges": row["groupe_charges"],
                "montant": part
            })

    df_rep = pd.DataFrame(repartitions)

    # =========================
    # AGRÉGATION PAR PROPRIÉTAIRE
    # =========================
    df_pivot = (
        df_rep
        .pivot_table(
            index="proprietaire",
            columns="groupe_charges",
            values="montant",
            aggfunc="sum",
            fill_value=0
        )
        .reset_index()
    )

    # Renommage des colonnes
    df_pivot.rename(columns=GROUPES_CHARGES, inplace=True)

    # =========================
    # LOI ALUR + TOTAUX
    # =========================
    charges_cols = list(GROUPES_CHARGES.values())

    df_pivot["Total charges"] = df_pivot[charges_cols].sum(axis=1)
    df_pivot["Loi ALUR (5%)"] = df_pivot["Total charges"] * 0.05
    df_pivot["Total à appeler"] = (
        df_pivot["Total charges"] + df_pivot["Loi ALUR (5%)"]
    )
    df_pivot["Appel trimestriel"] = df_pivot["Total à appeler"] / 4

    # =========================
    # AFFICHAGE
    # =========================
    st.markdown("### 📋 Détail par propriétaire")



# =========================
    # LIGNE DE TOTAUX
    # =========================
    total_row = {"proprietaire": "TOTAL"}

    for col in df_pivot.columns:
        if col != "proprietaire":
            total_row[col] = df_pivot[col].sum()

    df_pivot = pd.concat(
        [df_pivot, pd.DataFrame([total_row])],
        ignore_index=True
    )


    st.dataframe(
        df_pivot.style.format(
            {col: euro for col in df_pivot.columns if col != "proprietaire"}
        ),
        use_container_width=True
    )