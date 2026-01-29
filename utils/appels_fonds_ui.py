
import streamlit as st
import pandas as pd

# -------------------------
# Helpers
# -------------------------
def euro(x):
    if pd.isna(x):
        return "0 €"
    return f"{x:,.2f} €".replace(",", " ").replace(".", ",")

# -------------------------
# UI
# -------------------------
def appels_fonds_ui(supabase, annee):
    st.header("📢 Appels de fonds")

    # =========================
    # CHARGEMENT DONNÉES
    # =========================
    budgets = supabase.table("budgets").select("*").eq("annee", annee).execute().data
    plan = supabase.table("plan_comptable").select("groupe_compte, groupe_charges").execute().data

    if not budgets:
        st.warning("Aucun budget défini pour cette année.")
        return

    df_budget = pd.DataFrame(budgets)
    df_plan = pd.DataFrame(plan)

    # =========================
    # RATTACHEMENT GROUPE CHARGES
    # =========================
    df = df_budget.merge(
        df_plan,
        on="groupe_compte",
        how="left"
    )

    # =========================
    # MAPPING GROUPE CHARGES
    # =========================
    mapping = {
        1: "Charges communes générales",
        2: "Charges spéciales RDC / sous-sols",
        3: "Charges spéciales sous-sols",
        4: "Ascenseurs",
        5: "Monte voiture"
    }

    df["groupe_charges_libelle"] = df["groupe_charges"].map(mapping)

    # =========================
    # CALCUL BUDGET PAR GROUPE
    # =========================
    recap = (
        df.groupby("groupe_charges_libelle", dropna=False)["budget"]
        .sum()
        .reset_index()
        .rename(columns={
            "groupe_charges_libelle": "Groupe de charges",
            "budget": "Budget annuel"
        })
    )

    # =========================
    # LOI ALUR
    # =========================
    total_budget = recap["Budget annuel"].sum()
    loi_alur = total_budget * 0.05

    recap = pd.concat([
        recap,
        pd.DataFrame([{
            "Groupe de charges": "Loi ALUR (5 %)",
            "Budget annuel": loi_alur
        }])
    ], ignore_index=True)

    # =========================
    # TOTAL
    # =========================
    total_appels = recap["Budget annuel"].sum()

    recap = pd.concat([
        recap,
        pd.DataFrame([{
            "Groupe de charges": "TOTAL APPELS DE FONDS",
            "Budget annuel": total_appels
        }])
    ], ignore_index=True)

    # =========================
    # AFFICHAGE
    # =========================
    st.subheader(f"📆 Année {annee}")

    recap_display = recap.copy()
    recap_display["Budget annuel"] = recap_display["Budget annuel"].apply(euro)

    st.dataframe(
        recap_display,
        use_container_width=True,
        hide_index=True
    )

    st.info("💡 La ligne **Loi ALUR** correspond automatiquement à 5 % du budget annuel.")