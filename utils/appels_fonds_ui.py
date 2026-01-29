import streamlit as st
import pandas as pd
from io import BytesIO


# ======================================================
# CALCUL DES APPELS DE FONDS
# ======================================================
def calcul_appels_fonds(df_lots, total_charges):
    total_tantiemes = df_lots["tantiemes"].sum()

    df = df_lots.copy()

    df["charges"] = (
        df["tantiemes"] / total_tantiemes * total_charges
    )

    df["loi_alur"] = df["charges"] * 0.05
    df["total_appele"] = df["charges"] + df["loi_alur"]

    return df


# ======================================================
# UI – APPELS DE FONDS
# ======================================================
def appels_fonds_ui(supabase, annee):
    st.header("💸 Appels de fonds")

    # ======================================================
    # CHARGEMENT DES DONNÉES
    # ======================================================
    lots = supabase.table("lots").select(
        "lot_id, lot, tantiemes"
    ).execute()

    depenses = supabase.table("depenses").select(
        "annee, montant_ttc"
    ).eq("annee", annee).execute()

    if not lots.data:
        st.warning("Aucun lot trouvé.")
        return

    if not depenses.data:
        st.warning("Aucune dépense trouvée pour cette année.")
        return

    df_lots = pd.DataFrame(lots.data)
    df_dep = pd.DataFrame(depenses.data)

    total_charges = df_dep["montant_ttc"].sum()

    st.metric(
        "Total des charges de l’année",
        f"{total_charges:,.2f} €".replace(",", " ").replace(".", ",")
    )

    # ======================================================
    # CALCUL
    # ======================================================
    df = calcul_appels_fonds(df_lots, total_charges)

    # ======================================================
    # AFFICHAGE
    # ======================================================
    st.subheader("📊 Répartition des appels de fonds")

    df_display = df[[
        "lot",
        "tantiemes",
        "charges",
        "loi_alur",
        "total_appele"
    ]].copy()

    df_display.loc["TOTAL"] = [
        "TOTAL",
        df_display["tantiemes"].sum(),
        df_display["charges"].sum(),
        df_display["loi_alur"].sum(),
        df_display["total_appele"].sum(),
    ]

    st.dataframe(
        df_display.style.format({
            "charges": "{:,.2f} €".format,
            "loi_alur": "{:,.2f} €".format,
            "total_appele": "{:,.2f} €".format,
        }),
        use_container_width=True
    )

    # ======================================================
    # EXPORT EXCEL
    # ======================================================
    st.divider()
    st.subheader("📥 Export")

    output = BytesIO()

    with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
        df_display.to_excel(
            writer,
            index=False,
            sheet_name="Appels de fonds"
        )

    st.download_button(
        label="📥 Télécharger l’appel de fonds (Excel)",
        data=output.getvalue(),
        file_name=f"appel_fonds_{annee}.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )