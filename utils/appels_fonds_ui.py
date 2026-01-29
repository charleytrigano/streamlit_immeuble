import streamlit as st
import pandas as pd


def euro(x):
    return f"{x:,.2f} €".replace(",", " ").replace(".", ",")


def appels_fonds_ui(supabase, annee):
    st.header("💸 Appels de fonds")

    # =========================
    # CHARGEMENT DES DONNÉES
    # =========================
    dep = supabase.table("v_depenses_enrichies") \
        .select("annee, lot_id, montant_ttc") \
        .eq("annee", annee) \
        .execute()

    lots = supabase.table("lots") \
        .select("lot_id, lot, tantiemes") \
        .execute()

    if not dep.data or not lots.data:
        st.warning("Aucune donnée disponible.")
        return

    df_dep = pd.DataFrame(dep.data)
    df_lots = pd.DataFrame(lots.data)

    # =========================
    # CALCULS
    # =========================
    total_charges = df_dep["montant_ttc"].sum()
    total_tantiemes = df_lots["tantiemes"].sum()

    df = df_lots.copy()

    df["charges"] = (
        df["tantiemes"] / total_tantiemes * total_charges
    )

    df["loi_alur"] = df["charges"] * 0.05
    df["total_appele"] = df["charges"] + df["loi_alur"]

    # =========================
    # AFFICHAGE
    # =========================
    st.subheader(f"📅 Année {annee}")

    col1, col2, col3 = st.columns(3)
    col1.metric("💰 Charges totales", euro(total_charges))
    col2.metric("⚖️ Total tantièmes", f"{total_tantiemes:,.0f}")
    col3.metric("📤 Total appelé", euro(df['total_appele'].sum()))

    st.divider()

    display_df = df[[
        "lot",
        "tantiemes",
        "charges",
        "loi_alur",
        "total_appele"
    ]].copy()

    display_df.columns = [
        "Lot",
        "Tantièmes",
        "Charges",
        "Loi ALUR (5 %)",
        "Total appelé"
    ]

    for col in ["Charges", "Loi ALUR (5 %)", "Total appelé"]:
        display_df[col] = display_df[col].apply(euro)

    st.dataframe(
        display_df,
        use_container_width=True,
        hide_index=True
    )