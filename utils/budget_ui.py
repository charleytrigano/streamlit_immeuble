import streamlit as st
import pandas as pd


def euro(x):
    if x is None:
        return "0,00 €"
    return f"{x:,.2f} €".replace(",", " ").replace(".", ",")


def budget_ui(supabase, annee: int):
    st.header("💰 Budget annuel")
    st.caption(f"Année : **{annee}**")

    # ======================================================
    # PLAN COMPTABLE (pour auto-libellé)
    # ======================================================
    plan_res = supabase.table("plan_comptable").select(
        "groupe_compte, libelle_groupe"
    ).execute()

    df_plan = pd.DataFrame(plan_res.data or [])

    # dictionnaire groupe -> libellé
    plan_map = {}
    if not df_plan.empty:
        plan_map = (
            df_plan
            .dropna(subset=["groupe_compte"])
            .drop_duplicates("groupe_compte")
            .set_index("groupe_compte")["libelle_groupe"]
            .to_dict()
        )

    # ======================================================
    # BUDGETS DE L'ANNÉE
    # ======================================================
    bud_res = (
        supabase
        .table("budgets")
        .select("*")
        .eq("annee", annee)
        .execute()
    )

    df = pd.DataFrame(bud_res.data or [])

    # ======================================================
    # KPI
    # ======================================================
    total_budget = df["budget"].sum() if not df.empty else 0
    nb_groupes = df["groupe_compte"].nunique() if not df.empty else 0
    budget_moyen = total_budget / nb_groupes if nb_groupes else 0

    c1, c2, c3 = st.columns(3)
    c1.metric("💰 Budget total", euro(total_budget))
    c2.metric("📂 Groupes budgétés", nb_groupes)
    c3.metric("📊 Budget moyen", euro(budget_moyen))

    st.divider()

    # ======================================================
    # AJOUT BUDGET
    # ======================================================
    with st.expander("➕ Ajouter un budget"):
        with st.form("add_budget"):
            groupe = st.text_input("Groupe de compte (ex : 601)")
            libelle_auto = plan_map.get(groupe)

            st.text_input(
                "Libellé du groupe",
                value=libelle_auto or "",
                disabled=True
            )

            montant = st.number_input(
                "Montant du budget (€)",
                min_value=0.0,
                step=100.0
            )

            submit = st.form_submit_button("Ajouter")

            if submit:
                if not groupe:
                    st.error("Groupe de compte obligatoire.")
                elif groupe not in plan_map:
                    st.error("Groupe de compte inexistant dans le plan comptable.")
                elif montant <= 0:
                    st.error("Montant invalide.")
                else:
                    supabase.table("budgets").insert({
                        "annee": annee,
                        "groupe_compte": groupe,
                        "libelle_groupe": plan_map[groupe],
                        "budget": montant
                    }).execute()
                    st.success("✅ Budget ajouté.")
                    st.rerun()

    # ======================================================
    # LISTE / MODIFICATION / SUPPRESSION
    # ======================================================
    if df.empty:
        st.info("Aucun budget enregistré pour cette année.")
        return

    st.subheader("📋 Budgets par groupe")

    df = df.sort_values("groupe_compte")

    for _, row in df.iterrows():
        with st.container(border=True):
            col1, col2, col3, col4 = st.columns([2, 4, 3, 2])

            col1.write(f"**{row['groupe_compte']}**")
            col2.write(row.get("libelle_groupe", ""))
            col3.write(euro(row["budget"]))

            edit_key = f"edit_{row['id']}"
            if col4.button("✏️ Modifier", key=edit_key):
                st.session_state[edit_key] = True

            if st.session_state.get(edit_key):
                with st.form(f"form_{row['id']}"):
                    new_budget = st.number_input(
                        "Budget (€)",
                        value=float(row["budget"]),
                        min_value=0.0,
                        step=100.0
                    )

                    b1, b2, b3 = st.columns(3)
                    save = b1.form_submit_button("💾 Enregistrer")
                    delete = b2.form_submit_button("🗑️ Supprimer")
                    cancel = b3.form_submit_button("❌ Annuler")

                    if save:
                        supabase.table("budgets").update({
                            "budget": new_budget
                        }).eq("id", row["id"]).execute()
                        st.success("Budget modifié.")
                        st.rerun()

                    if delete:
                        supabase.table("budgets").delete() \
                            .eq("id", row["id"]).execute()
                        st.success("Budget supprimé.")
                        st.rerun()

                    if cancel:
                        st.session_state[edit_key] = False
                        st.rerun()