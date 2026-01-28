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
    bud_res = (
        supabase
        .table("budgets")
        .select("*")
        .eq("annee", annee)
        .execute()
    )
    df_bud = pd.DataFrame(bud_res.data)

    plan_res = (
        supabase
        .table("plan_comptable")
        .select("groupe_compte, libelle_groupe")
        .execute()
    )
    df_plan = pd.DataFrame(plan_res.data)

    if not df_plan.empty:
        df_plan = df_plan.drop_duplicates("groupe_compte")

    # ======================================================
    # AJOUT BUDGET
    # ======================================================
    st.subheader("➕ Ajouter un budget")

    groupes = sorted(df_plan["groupe_compte"].dropna().unique().tolist())

    with st.form("add_budget"):
        col1, col2, col3 = st.columns(3)

        groupe = col1.selectbox("Groupe de compte", options=groupes)

        libelle = ""
        if not df_plan.empty and groupe:
            lib = df_plan[df_plan["groupe_compte"] == groupe]["libelle_groupe"]
            libelle = lib.iloc[0] if not lib.empty else ""

        col2.text_input(
            "Libellé groupe",
            value=libelle,
            disabled=True
        )

        montant = col3.number_input(
            "Budget annuel (€)",
            min_value=0.0,
            step=100.0
        )

        submit = st.form_submit_button("➕ Ajouter")

        if submit:
            supabase.table("budgets").insert({
                "annee": annee,
                "groupe_compte": groupe,
                "libelle_groupe": libelle,
                "budget": montant
            }).execute()

            st.success("Budget ajouté")
            st.rerun()

    # ======================================================
    # TABLEAU BUDGET
    # ======================================================
    st.subheader(f"📊 Budget {annee}")

    if df_bud.empty:
        st.info("Aucun budget enregistré pour cette année.")
        return

    df_bud = df_bud.sort_values("groupe_compte")

    total_budget = df_bud["budget"].fillna(0).sum()

    st.metric("💰 Budget total", euro(total_budget))

    # ======================================================
    # LISTE / MODIFICATION / SUPPRESSION
    # ======================================================
    for _, row in df_bud.iterrows():
        with st.expander(
            f"{row['groupe_compte']} — {row.get('libelle_groupe', '')} "
            f"({euro(row['budget'])})"
        ):

            budget_val = row["budget"] if row["budget"] is not None else 0.0

            col1, col2, col3 = st.columns([2, 2, 1])

            # -------- MODIFIER --------
            if col1.button("✏️ Modifier", key=f"edit_{row['id']}"):
                st.session_state[f"edit_{row['id']}"] = True

            # -------- SUPPRIMER --------
            if col2.button("🗑️ Supprimer", key=f"del_{row['id']}"):
                supabase.table("budgets").delete().eq("id", row["id"]).execute()
                st.warning("Budget supprimé")
                st.rerun()

            # -------- FORM EDIT --------
            if st.session_state.get(f"edit_{row['id']}"):
                new_budget = st.number_input(
                    "Nouveau budget (€)",
                    min_value=0.0,
                    step=100.0,
                    value=float(budget_val),
                    key=f"nb_{row['id']}"
                )

                col_ok, col_cancel = st.columns(2)

                if col_ok.button("💾 Enregistrer", key=f"save_{row['id']}"):
                    supabase.table("budgets").update({
                        "budget": new_budget
                    }).eq("id", row["id"]).execute()

                    st.success("Budget mis à jour")
                    st.session_state.pop(f"edit_{row['id']}", None)
                    st.rerun()

                if col_cancel.button("❌ Annuler", key=f"cancel_{row['id']}"):
                    st.session_state.pop(f"edit_{row['id']}", None)
                    st.rerun()