import streamlit as st
import pandas as pd
from datetime import datetime


def budget_ui(supabase):
    st.title("💰 Budget annuel")

    # =========================
    # 1. CHARGEMENT DES DONNÉES
    # =========================
    resp = supabase.table("budgets").select("*").execute()
    data = resp.data or []

    df = pd.DataFrame(data)

    # Normalisation minimale
    if df.empty:
        df = pd.DataFrame(columns=["id", "annee", "compte", "budget", "groupe_compte", "created_at"])

    df["annee"] = pd.to_numeric(df["annee"], errors="coerce").astype("Int64")
    df["budget"] = pd.to_numeric(df["budget"], errors="coerce").fillna(0)
    df["compte"] = df["compte"].astype(str)

    # =========================
    # 2. ANNÉES DISPONIBLES (CORRECTIF CLÉ)
    # =========================
    current_year = datetime.now().year

    years_from_db = sorted(df["annee"].dropna().unique().tolist())
    years_auto = [current_year - 1, current_year, current_year + 1]

    years = sorted(set(years_from_db + years_auto))

    selected_year = st.selectbox(
        "Année budgétaire",
        years,
        index=years.index(current_year) if current_year in years else 0,
    )

    # =========================
    # 3. FILTRAGE PAR ANNÉE
    # =========================
    df_year = df[df["annee"] == selected_year].copy()

    # =========================
    # 4. KPI
    # =========================
    col1, col2, col3 = st.columns(3)

    total_budget = df_year["budget"].sum()
    nb_comptes = df_year["compte"].nunique()
    budget_moyen = total_budget / nb_comptes if nb_comptes > 0 else 0

    col1.metric("Budget total (€)", f"{total_budget:,.2f}")
    col2.metric("Nombre de comptes", nb_comptes)
    col3.metric("Budget moyen (€)", f"{budget_moyen:,.2f}")

    st.divider()

    # =========================
    # 5. ONGLETS
    # =========================
    tab_consult, tab_add, tab_edit, tab_delete = st.tabs(
        ["📊 Consulter", "➕ Ajouter", "✏️ Modifier", "🗑 Supprimer"]
    )

    # =========================
    # 5.1 CONSULTER
    # =========================
    with tab_consult:
        if df_year.empty:
            st.info("Aucun budget pour cette année.")
        else:
            st.dataframe(
                df_year[["annee", "compte", "budget", "groupe_compte"]],
                use_container_width=True,
            )

    # =========================
    # 5.2 AJOUTER
    # =========================
    with tab_add:
        st.subheader("Ajouter un budget")

        with st.form("add_budget_form"):
            compte = st.text_input("Compte")
            budget = st.number_input("Budget (€)", min_value=0.0, step=50.0)
            groupe = st.text_input("Groupe de compte", value=compte)

            submitted = st.form_submit_button("Enregistrer")

            if submitted:
                if not compte:
                    st.error("Le compte est obligatoire.")
                else:
                    supabase.table("budgets").insert(
                        {
                            "annee": int(selected_year),
                            "compte": compte,
                            "budget": float(budget),
                            "groupe_compte": groupe,
                        }
                    ).execute()

                    st.success("Budget ajouté.")
                    st.rerun()

    # =========================
    # 5.3 MODIFIER
    # =========================
    with tab_edit:
        st.subheader("Modifier un budget")

        if df_year.empty:
            st.info("Aucun budget à modifier.")
        else:
            row = st.selectbox(
                "Sélectionner un compte",
                df_year.to_dict("records"),
                format_func=lambda r: f"{r['compte']} – {r['budget']} €",
            )

            with st.form("edit_budget_form"):
                new_budget = st.number_input(
                    "Nouveau budget (€)",
                    value=float(row["budget"]),
                    min_value=0.0,
                    step=50.0,
                )
                new_group = st.text_input(
                    "Groupe de compte",
                    value=row.get("groupe_compte") or row["compte"],
                )

                submitted = st.form_submit_button("Mettre à jour")

                if submitted:
                    supabase.table("budgets").update(
                        {
                            "budget": float(new_budget),
                            "groupe_compte": new_group,
                        }
                    ).eq("id", row["id"]).execute()

                    st.success("Budget mis à jour.")
                    st.rerun()

    # =========================
    # 5.4 SUPPRIMER
    # =========================
    with tab_delete:
        st.subheader("Supprimer un budget")

        if df_year.empty:
            st.info("Aucun budget à supprimer.")
        else:
            row = st.selectbox(
                "Sélectionner un compte à supprimer",
                df_year.to_dict("records"),
                format_func=lambda r: f"{r['compte']} – {r['budget']} €",
            )

            if st.button("❌ Supprimer définitivement"):
                supabase.table("budgets").delete().eq("id", row["id"]).execute()
                st.success("Budget supprimé.")
                st.rerun()