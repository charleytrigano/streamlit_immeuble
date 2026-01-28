import streamlit as st
import pandas as pd

# =========================
# FORMAT €
# =========================
def euro(x):
    try:
        return f"{float(x):,.2f} €".replace(",", " ").replace(".", ",")
    except Exception:
        return "0,00 €"


# =========================
# UI BUDGET
# =========================
def budget_ui(supabase, annee):
    st.header("💰 Budget")

    # ======================================================
    # CHARGEMENT DES DONNÉES
    # ======================================================
    df_bud = pd.DataFrame(
        supabase
        .table("budgets")
        .select("*")
        .eq("annee", annee)
        .execute()
        .data
    )

    df_plan = pd.DataFrame(
        supabase
        .table("plan_comptable")
        .select("groupe_compte, libelle_groupe")
        .execute()
        .data
    )

    if not df_plan.empty:
        df_plan = df_plan.drop_duplicates("groupe_compte")

    # ======================================================
    # KPI
    # ======================================================
    if not df_bud.empty:
        total_budget = df_bud["budget"].fillna(0).sum()
    else:
        total_budget = 0

    st.metric("💰 Budget total", euro(total_budget))

    # ======================================================
    # TABLEAU DES LIGNES DE BUDGET
    # ======================================================
    st.subheader(f"📄 Lignes de budget — {annee}")

    if df_bud.empty:
        st.info("Aucune ligne de budget pour cette année.")
    else:
        df_display = (
            df_bud[[
                "groupe_compte",
                "libelle_groupe",
                "budget"
            ]]
            .sort_values("groupe_compte")
            .rename(columns={
                "groupe_compte": "Groupe de compte",
                "libelle_groupe": "Libellé groupe",
                "budget": "Budget (€)"
            })
        )

        st.dataframe(
            df_display,
            use_container_width=True
        )

    st.divider()

    # ======================================================
    # AJOUT BUDGET
    # ======================================================
    st.subheader("➕ Ajouter un budget")

    groupes = sorted(df_plan["groupe_compte"].dropna().unique().tolist())

    with st.form("add_budget"):
        col1, col2, col3 = st.columns(3)

        groupe = col1.selectbox("Groupe de compte", groupes)

        libelle = ""
        lib = df_plan[df_plan["groupe_compte"] == groupe]["libelle_groupe"]
        if not lib.empty:
            libelle = lib.iloc[0]

        col2.text_input("Libellé groupe", libelle, disabled=True)

        montant = col3.number_input(
            "Budget annuel (€)",
            min_value=0.0,
            step=100.0
        )

        if st.form_submit_button("➕ Ajouter"):
            supabase.table("budgets").insert({
                "annee": annee,
                "groupe_compte": groupe,
                "libelle_groupe": libelle,
                "budget": montant
            }).execute()

            st.success("Budget ajouté")
            st.rerun()

    st.divider()

    # ======================================================
    # MODIFICATION / SUPPRESSION
    # ======================================================
    if df_bud.empty:
        return

    st.subheader("✏️ Modifier / 🗑️ Supprimer un budget")

    df_bud["label"] = (
        df_bud["groupe_compte"]
        + " — "
        + df_bud["libelle_groupe"].fillna("")
    )

    choix = st.selectbox(
        "Sélectionner une ligne de budget",
        options=df_bud["label"].tolist()
    )

    row = df_bud[df_bud["label"] == choix].iloc[0]

    col1, col2, col3 = st.columns(3)

    new_budget = col1.number_input(
        "Budget (€)",
        min_value=0.0,
        step=100.0,
        value=float(row["budget"])
    )

    col2.text_input("Groupe", row["groupe_compte"], disabled=True)
    col3.text_input("Libellé", row["libelle_groupe"], disabled=True)

    col_save, col_del = st.columns(2)

    if col_save.button("💾 Enregistrer"):
        supabase.table("budgets").update({
            "budget": new_budget
        }).eq("id", row["id"]).execute()

        st.success("Budget mis à jour")
        st.rerun()

    if col_del.button("🗑️ Supprimer"):
        supabase.table("budgets").delete().eq("id", row["id"]).execute()
        st.warning("Budget supprimé")
        st.rerun()