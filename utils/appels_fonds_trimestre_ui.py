import streamlit as st
import pandas as pd

BASE_TANTIEMES = 10_000
TAUX_LOI_ALUR = 0.05

GROUPES_LABELS = {
    "1": "Charges communes générales",
    "2": "Charges spéciales RDC / sous-sols",
    "3": "Charges spéciales sous-sols",
    "4": "Ascenseurs",
    "5": "Monte-voiture",
}


def euro(x):
    return f"{x:,.2f} €".replace(",", " ").replace(".", ",")


def appels_fonds_trimestre_ui(supabase, annee):
    st.header("📢 Appels de fonds – Répartition trimestrielle")

    # ======================================================
    # CHARGEMENT DES DONNÉES
    # ======================================================
    df_bud = pd.DataFrame(
        supabase.table("budgets")
        .select("*")
        .eq("annee", annee)
        .execute()
        .data
    )

    df_lots = pd.DataFrame(
        supabase.table("lots")
        .select("lot_id, lot, proprietaire, tantiemes")
        .execute()
        .data
    )

    if df_bud.empty:
        st.warning("Aucun budget enregistré pour cette année.")
        return

    if df_lots.empty:
        st.warning("Aucun lot enregistré.")
        return

    # Sécurisation
    df_lots["tantiemes"] = pd.to_numeric(df_lots["tantiemes"], errors="coerce").fillna(0)

    total_tantiemes = df_lots["tantiemes"].sum()
    if total_tantiemes == 0:
        st.error("Le total des tantièmes est nul.")
        return

    # ======================================================
    # BUDGET ANNUEL PAR GROUPE
    # ======================================================
    bud_groupes = (
        df_bud
        .groupby(["groupe_compte", "libelle_groupe"], as_index=False)
        .agg(budget_annuel=("budget", "sum"))
    )

    # ======================================================
    # CALCUL DES APPELS PAR LOT / GROUPE
    # ======================================================
    lignes = []

    for _, bud in bud_groupes.iterrows():
        groupe = str(bud["groupe_compte"])
        budget_annuel = bud["budget_annuel"]
        budget_trimestre = budget_annuel / 4

        for _, lot in df_lots.iterrows():
            part = lot["tantiemes"] / total_tantiemes
            montant = budget_trimestre * part

            lignes.append({
                "lot_id": lot["lot_id"],
                "lot": lot["lot"],
                "proprietaire": lot["proprietaire"],
                "groupe_charges": GROUPES_LABELS.get(groupe, f"Groupe {groupe}"),
                "appel_trimestriel": montant
            })

    df_appels = pd.DataFrame(lignes)

    # ======================================================
    # TOTAL PAR LOT
    # ======================================================
    df_total_lot = (
        df_appels
        .groupby(["lot_id", "lot", "proprietaire"], as_index=False)
        .agg(total_trimestre=("appel_trimestriel", "sum"))
    )

    # ======================================================
    # LOI ALUR – 5 %
    # ======================================================
    alur_lignes = []
    for _, row in df_total_lot.iterrows():
        alur_lignes.append({
            "lot_id": row["lot_id"],
            "lot": row["lot"],
            "proprietaire": row["proprietaire"],
            "Loi ALUR (5 %)": row["total_trimestre"] * TAUX_LOI_ALUR
        })

    df_alur = pd.DataFrame(alur_lignes)

    # ======================================================
    # AFFICHAGE
    # ======================================================
    col1, col2, col3 = st.columns(3)

    col1.metric(
        "Budget annuel",
        euro(df_bud["budget"].sum())
    )

    col2.metric(
        "Appels trimestriels totaux",
        euro(df_total_lot["total_trimestre"].sum())
    )

    col3.metric(
        "Loi ALUR (5 %)",
        euro(df_alur["Loi ALUR (5 %)"].sum())
    )

    st.markdown("### 📋 Détail des appels par groupe et par lot")
    st.dataframe(
        df_appels.sort_values(["lot", "groupe_charges"]),
        use_container_width=True
    )

    st.markdown("### 🧾 Total des appels par lot (trimestre)")
    st.dataframe(
        df_total_lot.sort_values("lot"),
        use_container_width=True
    )

    st.markdown("### ⚖️ Ligne Loi ALUR (5 %)")
    st.dataframe(
        df_alur.sort_values("lot"),
        use_container_width=True
    )