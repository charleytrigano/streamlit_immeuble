import streamlit as st
import pandas as pd

from utils.appels_fonds_pdf import generate_pdf_appel_fonds


def euro(x):
    return f"{x:,.2f} €".replace(",", " ").replace(".", ",")


def appels_fonds_trimestre_ui(supabase, annee):
    st.header("📢 Appels de fonds trimestriels")

    # ======================================================
    # CHOIX DU TRIMESTRE
    # ======================================================
    trimestre = st.selectbox(
        "Trimestre",
        options=[1, 2, 3, 4],
        index=0
    )

    # ======================================================
    # CHARGEMENT DES DONNÉES
    # ======================================================
    bud = supabase.table("budgets").select("*").eq("annee", annee).execute().data
    dep = supabase.table("depenses").select("*").eq("annee", annee).execute().data
    lots = supabase.table("lots").select("*").execute().data
    plan = supabase.table("plan_comptable").select("*").execute().data

    if not bud or not lots:
        st.warning("Aucune donnée budget ou lots disponible.")
        return

    df_bud = pd.DataFrame(bud)
    df_dep = pd.DataFrame(dep)
    df_lots = pd.DataFrame(lots)
    df_plan = pd.DataFrame(plan)

    # ======================================================
    # BUDGET ANNUEL & TRIMESTRIEL
    # ======================================================
    budget_annuel = df_bud["budget"].sum()
    budget_trimestriel = budget_annuel / 4
    loi_alur_total = budget_trimestriel * 0.05

    st.metric("Budget annuel", euro(budget_annuel))
    st.metric("Appel trimestriel (hors ALUR)", euro(budget_trimestriel))
    st.metric("Loi ALUR (5 %)", euro(loi_alur_total))

    # ======================================================
    # PRÉPARATION RÉPARTITION PAR LOT
    # ======================================================
    # Nettoyage
    df_lots["tantiemes"] = pd.to_numeric(df_lots["tantiemes"], errors="coerce").fillna(0)
    total_tantiemes = df_lots["tantiemes"].sum()

    if total_tantiemes == 0:
        st.error("Total tantièmes = 0 → impossible de répartir.")
        return

    # Quote-part lot
    df_lots["quote_part"] = df_lots["tantiemes"] / total_tantiemes
    df_lots["appel_trimestriel"] = df_lots["quote_part"] * budget_trimestriel
    df_lots["alur"] = df_lots["appel_trimestriel"] * 0.05
    df_lots["appel_total"] = df_lots["appel_trimestriel"] + df_lots["alur"]

    # ======================================================
    # TABLEAU GLOBAL
    # ======================================================
    st.subheader("📋 Appels de fonds par lot")

    st.dataframe(
        df_lots[[
            "lot_id",
            "lot",
            "proprietaire",
            "appel_trimestriel",
            "alur",
            "appel_total"
        ]].rename(columns={
            "lot_id": "Lot ID",
            "lot": "Lot",
            "proprietaire": "Propriétaire",
            "appel_trimestriel": "Appel trimestriel (€)",
            "alur": "Loi ALUR (€)",
            "appel_total": "Total à appeler (€)"
        }).sort_values("Lot"),
        use_container_width=True
    )

    # ======================================================
    # PDF PAR PROPRIÉTAIRE
    # ======================================================
    st.subheader("📄 PDF par propriétaire")

    proprietaires = df_lots["proprietaire"].dropna().unique().tolist()

    for prop in proprietaires:
        df_p = df_lots[df_lots["proprietaire"] == prop]

        total_prop = df_p["appel_trimestriel"].sum()
        alur_prop = df_p["alur"].sum()

        # Détail par groupe de charges (basé sur le budget)
        df_bud_grp = (
            df_bud
            .groupby(["groupe_compte", "libelle_groupe"], as_index=False)
            .agg(budget=("budget", "sum"))
        )
        df_bud_grp["trimestre"] = df_bud_grp["budget"] / 4
        df_bud_grp["part_prop"] = df_bud_grp["trimestre"] * (total_prop / budget_trimestriel)

        lignes_detail = [
            {
                "libelle": row["libelle_groupe"],
                "montant": row["part_prop"]
            }
            for _, row in df_bud_grp.iterrows()
        ]

        col1, col2 = st.columns([3, 1])
        col1.markdown(f"**{prop}** — {euro(total_prop + alur_prop)}")

        if col2.button("📄 PDF", key=f"pdf_{prop}"):
            pdf = generate_pdf_appel_fonds(
                proprietaire=prop,
                annee=annee,
                trimestre=trimestre,
                lignes_detail=lignes_detail,
                total_trimestre=total_prop,
                loi_alur=alur_prop
            )

            st.download_button(
                label="⬇️ Télécharger le PDF",
                data=pdf,
                file_name=f"appel_fonds_{prop}_{annee}_T{trimestre}.pdf",
                mime="application/pdf",
                key=f"dl_{prop}"
            )