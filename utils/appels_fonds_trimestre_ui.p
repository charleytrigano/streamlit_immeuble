import streamlit as st
import pandas as pd


def appels_fonds_trimestre_ui(supabase, annee: int):
    st.subheader("📊 Appels de fonds trimestriels")

    # =========================
    # 1️⃣ Requête Supabase
    # =========================
    res = (
        supabase
        .table("repartition_par_lot_controle")
        .select(
            "lot, groupe_compte, part_lot"
        )
        .eq("annee", annee)
        .execute()
    )

    if not res.data:
        st.warning("Aucune donnée de répartition pour cette année")
        return

    df = pd.DataFrame(res.data)

    # =========================
    # 2️⃣ Pivot : 1 ligne = 1 lot
    # =========================
    pivot = (
        df
        .pivot_table(
            index="lot",
            columns="groupe_compte",
            values="part_lot",
            aggfunc="sum",
            fill_value=0
        )
        .reset_index()
    )

    # =========================
    # 3️⃣ Renommage lisible
    # =========================
    mapping = {
        "601": "Charges générales",
        "602": "Charges spéciales sous-sol",
        "603": "Charges garages / parkings",
        "604": "Ascenseurs",
        "605": "Monte-voitures"
    }

    for code, label in mapping.items():
        if code not in pivot.columns:
            pivot[code] = 0.0

    pivot = pivot.rename(columns=mapping)

    # =========================
    # 4️⃣ Totaux & calculs
    # =========================
    pivot["Total charges"] = pivot[list(mapping.values())].sum(axis=1)

    pivot["Loi ALUR (5%)"] = pivot["Total charges"] * 0.05
    pivot["Total à appeler"] = pivot["Total charges"] + pivot["Loi ALUR (5%)"]
    pivot["Appel trimestriel"] = pivot["Total à appeler"] / 4

    # =========================
    # 5️⃣ Ligne TOTAL GÉNÉRAL
    # =========================
    total_row = {"lot": "TOTAL"}

    for col in pivot.columns:
        if col != "lot":
            total_row[col] = pivot[col].sum()

    pivot = pd.concat([pivot, pd.DataFrame([total_row])], ignore_index=True)

    # =========================
    # 6️⃣ Affichage
    # =========================
    st.dataframe(
        pivot.style.format("{:,.2f} €", subset=pivot.columns[1:]),
        use_container_width=True
    )

    # =========================
    # 7️⃣ Contrôle de cohérence
    # =========================
    budget_total = pivot.loc[pivot["lot"] == "TOTAL", "Total charges"].values[0]

    st.info(f"💰 Total charges réparties : **{budget_total:,.2f} €**")
