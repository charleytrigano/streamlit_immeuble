import streamlit as st
import pandas as pd

# ======================================
# APPELS DE FONDS PAR TRIMESTRE
# ======================================
def appels_fonds_trimestre_ui(supabase, annee):
    st.subheader(f"📢 Appels de fonds par trimestre – Année {annee}")

    # ----------------------------------
    # Chargement du budget annuel par groupe de charges
    # ----------------------------------
    res = (
        supabase
        .table("v_budget_par_groupe_charges")
        .select("groupe_charges, budget_annuel")
        .eq("annee", annee)
        .execute()
    )

    if not res.data:
        st.warning("Aucun budget trouvé pour cette année")
        return

    df = pd.DataFrame(res.data)

    # ----------------------------------
    # Mapping groupes de charges
    # ----------------------------------
    groupes_labels = {
        1: "Charges communes générales",
        2: "Charges communes RDC / sous-sols",
        3: "Charges spéciales sous-sols",
        4: "Ascenseurs",
        5: "Monte-voitures",
    }

    df["Libellé"] = df["groupe_charges"].map(groupes_labels)
    df["Budget annuel (€)"] = df["budget_annuel"].round(2)

    # ----------------------------------
    # Calcul appel trimestriel
    # ----------------------------------
    df["Appel trimestriel (€)"] = (df["Budget annuel (€)"] / 4).round(2)

    # ----------------------------------
    # Ligne Loi ALUR (5 % du budget total)
    # ----------------------------------
    total_budget = df["Budget annuel (€)"].sum()
    alur_annuel = round(total_budget * 0.05, 2)
    alur_trimestre = round(alur_annuel / 4, 2)

    df_alur = pd.DataFrame([{
        "groupe_charges": 99,
        "Libellé": "Loi ALUR (5 %)",
        "Budget annuel (€)": alur_annuel,
        "Appel trimestriel (€)": alur_trimestre,
    }])

    df = pd.concat([df, df_alur], ignore_index=True)

    # ----------------------------------
    # Totaux
    # ----------------------------------
    total_annuel = df["Budget annuel (€)"].sum()
    total_trimestriel = df["Appel trimestriel (€)"].sum()

    df_total = pd.DataFrame([{
        "Libellé": "TOTAL",
        "Budget annuel (€)": round(total_annuel, 2),
        "Appel trimestriel (€)": round(total_trimestriel, 2),
    }])

    df = pd.concat([df, df_total], ignore_index=True)

    # ----------------------------------
    # Affichage
    # ----------------------------------
    st.markdown("### 💰 Détail des appels de fonds")

    st.dataframe(
        df[[
            "Libellé",
            "Budget annuel (€)",
            "Appel trimestriel (€)"
        ]],
        use_container_width=True
    )

    # ----------------------------------
    # Résumé
    # ----------------------------------
    col1, col2 = st.columns(2)

    col1.metric(
        "Budget annuel total",
        f"{total_annuel:,.2f} €".replace(",", " ")
    )

    col2.metric(
        "Appel trimestriel total",
        f"{total_trimestriel:,.2f} €".replace(",", " ")
    )

    st.success("✅ Appels de fonds trimestriels calculés avec succès")