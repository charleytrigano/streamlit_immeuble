import streamlit as st
import pandas as pd


# ======================================================
# UI – APPELS DE FONDS PAR GROUPE DE CHARGES
# ======================================================
def appels_fonds_groupes_ui(supabase, annee):
    st.header("💸 Appels de fonds par groupe de charges")

    # =========================
    # CHARGEMENT DES DONNÉES
    # =========================
    dep = supabase.table("depenses").select(
        "annee, compte, montant_ttc"
    ).eq("annee", annee).execute()

    plan = supabase.table("plan_comptable").select(
        "compte_8, groupe_charges"
    ).execute()

    lots = supabase.table("lots").select(
        "lot_id, lot, tantiemes"
    ).execute()

    if not dep.data or not plan.data or not lots.data:
        st.warning("Données insuffisantes pour calculer les appels de fonds.")
        return

    df_dep = pd.DataFrame(dep.data)
    df_plan = pd.DataFrame(plan.data)
    df_lots = pd.DataFrame(lots.data)

    # =========================
    # NETTOYAGE
    # =========================
    df_dep["compte"] = df_dep["compte"].astype(str)
    df_plan["compte_8"] = df_plan["compte_8"].astype(str)

    # =========================
    # DÉPENSES → GROUPE DE CHARGES
    # =========================
    df = df_dep.merge(
        df_plan,
        left_on="compte",
        right_on="compte_8",
        how="left"
    )

    if df["groupe_charges"].isna().any():
        st.error("⚠️ Certaines dépenses ne sont pas rattachées à un groupe de charges.")
        st.dataframe(df[df["groupe_charges"].isna()])
        return

    # =========================
    # TOTAL PAR GROUPE DE CHARGES
    # =========================
    charges_groupes = (
        df.groupby("groupe_charges", as_index=False)
        .agg(charges=("montant_ttc", "sum"))
    )

    total_charges = charges_groupes["charges"].sum()

    st.metric(
        "Total charges",
        f"{total_charges:,.2f} €".replace(",", " ").replace(".", ",")
    )

    # =========================
    # RÉPARTITION PAR LOT
    # =========================
    total_tantiemes = df_lots["tantiemes"].sum()

    repartition = []

    for _, lot in df_lots.iterrows():
        for _, grp in charges_groupes.iterrows():
            part = grp["charges"] * lot["tantiemes"] / total_tantiemes
            repartition.append({
                "lot": lot["lot"],
                "groupe_charges": grp["groupe_charges"],
                "charges": part
            })

    df_rep = pd.DataFrame(repartition)

    # =========================
    # LOI ALUR
    # =========================
    df_rep["loi_alur"] = df_rep["charges"] * 0.05
    df_rep["total_appele"] = df_rep["charges"] + df_rep["loi_alur"]

    # =========================
    # AFFICHAGE
    # =========================
    st.subheader("📊 Appels de fonds par lot et groupe de charges")

    pivot = df_rep.pivot_table(
        index="lot",
        columns="groupe_charges",
        values="total_appele",
        aggfunc="sum"
    ).fillna(0)

    pivot["TOTAL LOT"] = pivot.sum(axis=1)

    pivot.loc["TOTAL GROUPE"] = pivot.sum()

    st.dataframe(
        pivot.style.format("{:,.2f} €".format),
        use_container_width=True
    )

    st.caption("Inclut la ligne Loi ALUR (5 %) sur chaque groupe de charges.")