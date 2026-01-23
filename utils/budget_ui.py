import streamlit as st
import pandas as pd
from decimal import Decimal

# =========================
# DATA ACCESS
# =========================

def load_budgets(supabase):
    res = supabase.table("budgets").select("*").execute()
    return pd.DataFrame(res.data or [])


def budget_exists(df, annee, compte):
    return not df[(df["annee"] == annee) & (df["compte"] == compte)].empty


# =========================
# UI
# =========================

def budget_ui(supabase):

    st.title("💰 Budget")
    df = load_budgets(supabase)

    # -------------------------
    # Année
    # -------------------------
    annees = sorted(df["annee"].unique().tolist()) if not df.empty else []
    annee = st.selectbox("Année budgétaire", annees)

    df_year = df[df["annee"] == annee] if annee else pd.DataFrame()

    # -------------------------
    # Onglets
    # -------------------------
    tab_consult, tab_add, tab_edit, tab_delete = st.tabs(
        ["📊 Consulter", "➕ Ajouter", "✏️ Modifier", "🗑 Supprimer"]
    )

    # =========================
    # CONSULTER
    # =========================
    with tab_consult:
        if df_year.empty:
            st.info("Aucun budget pour cette année.")
        else:
            total = df_year["budget"].sum()
            count = len(df_year)
            avg = total / count if count else 0

            c1, c2, c3 = st.columns(3)
            c1.metric("Budget total (€)", f"{total:,.2f}")
            c2.metric("Nombre de comptes", count)
            c3.metric("Budget moyen (€)", f"{avg:,.2f}")

            st.dataframe(
                df_year.sort_values("compte"),
                use_container_width=True,
                hide_index=True,
            )

    # =========================
    # AJOUTER
    # =========================
    with tab_add:
        st.subheader("Ajouter un budget")

        with st.form("add_budget_form", clear_on_submit=True):
            compte = st.text_input("Compte")
            budget = st.number_input("Budget (€)", min_value=0.0, step=100.0)
            submitted = st.form_submit_button("Enregistrer")

            if submitted:
                if not compte:
                    st.error("Le compte est obligatoire.")
                    return

                if budget_exists(df, annee, compte):
                    st.error(
                        f"Le compte {compte} existe déjà pour l'année {annee}."
                    )
                    return

                supabase.table("budgets").insert(
                    {
                        "annee": int(annee),
                        "compte": compte,
                        "budget": float(Decimal(budget)),
                    }
                ).execute()

                st.success("Budget ajouté.")
                st.rerun()

    # =========================
    # MODIFIER
    # =========================
    with tab_edit:
        st.subheader("Modifier un budget")

        if df_year.empty:
            st.info("Aucun budget à modifier.")
        else:
            row = st.selectbox(
                "Compte",
                df_year.to_dict("records"),
                format_func=lambda x: x["compte"],
            )

            with st.form("edit_budget_form"):
                new_budget = st.number_input(
                    "Nouveau budget (€)",
                    min_value=0.0,
                    value=float(row["budget"]),
                    step=100.0,
                )
                submitted = st.form_submit_button("Mettre à jour")

                if submitted:
                    supabase.table("budgets").update(
                        {"budget": float(Decimal(new_budget))}
                    ).eq("id", row["id"]).execute()

                    st.success("Budget modifié.")
                    st.rerun()

    # =========================
    # SUPPRIMER
    # =========================
    with tab_delete:
        st.subheader("Supprimer un budget")

        if df_year.empty:
            st.info("Aucun budget à supprimer.")
        else:
            row = st.selectbox(
                "Compte à supprimer",
                df_year.to_dict("records"),
                format_func=lambda x: x["compte"],
            )

            if st.button("Supprimer définitivement"):
                supabase.table("budgets").delete().eq("id", row["id"]).execute()
                st.success("Budget supprimé.")
                st.rerun()