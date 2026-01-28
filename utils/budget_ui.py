import streamlit as st
import pandas as pd


def euro(x):
    if x is None:
        return "0,00 €"
    return f"{x:,.2f} €".replace(",", " ").replace(".", ",")


def budget_ui(supabase, annee):
    st.header("💰 Budget annuel")

    # =============================
    # CHARGEMENT DES DONNÉES
    # =============================
    res = (
        supabase
        .table("budgets")
        .select("*")
        .eq("annee", annee)
        .execute()
    )

    data = res.data or []
    df = pd.DataFrame(data)

    st.caption(f"📌 Budgets trouvés : {len(df)} lignes")

    # =============================
    # KPI
    # =============================
    if not df.empty:
        total_budget = df["budget"].sum()
        nb_groupes = df["groupe_compte"].nunique()
        budget_moyen = total_budget / nb_groupes if nb_groupes else 0
    else:
        total_budget = 0
        nb_groupes = 0
        budget_moyen = 0

    k1, k2, k3 = st.columns(3)
    k1.metric("💰 Budget total", euro(total_budget))
    k2.metric("📂 Groupes", nb_groupes)
    k3.metric("📊 Budget moyen", euro(budget_moyen))

    st.divider()

    # =============================
    # AJOUT D’UN BUDGET
    # =============================
    with st.expander("➕ Ajouter un budget", expanded=False):
        with st.form("add_budget"):
            groupe = st.text_input("Groupe de compte (ex: 606)")
            libelle = st.text_input("Libellé groupe")
            montant = st.number_input("Montant (€)", min_value=0.0, step=100.0)

            submitted = st.form_submit_button("Ajouter")

            if submitted:
                if not groupe or montant <= 0:
                    st.error("Groupe et montant obligatoires")
                else:
                    supabase.table("budgets").insert({
                        "annee": annee,
                        "groupe_compte": groupe,
                        "libelle_groupe": libelle,
                        "budget": montant
                    }).execute()
                    st.success("Budget ajouté")
                    st.rerun()

    # =============================
    # TABLEAU + ACTIONS
    # =============================
    if df.empty:
        st.warning("Aucun budget défini pour cette année.")
        return

    st.subheader("📋 Budgets par groupe")

    for _, row in df.iterrows():
        with st.container(border=True):
            c1, c2, c3, c4 = st.columns([2, 3, 2, 2])

            c1.write(f"**{row['groupe_compte']}**")
            c2.write(row.get("libelle_groupe", ""))
            c3.write(euro(row["budget"]))

            # =============================
            # MODIFIER
            # =============================
            with c4:
                if st.button("✏️ Modifier", key=f"edit_{row['id']}"):
                    st.session_state[f"edit_{row['id']}"] = True

            if st.session_state.get(f"edit_{row['id']}"):
                with st.form(f"form_edit_{row['id']}"):
                    new_lib = st.text_input(
                        "Libellé",
                        value=row.get("libelle_groupe", "")
                    )
                    new_budget = st.number_input(
                        "Budget (€)",
                        value=float(row["budget"]),
                        min_value=0.0,
                        step=100.0
                    )

                    save = st.form_submit_button("💾 Enregistrer")
                    delete = st.form_submit_button("🗑️ Supprimer")

                    if save:
                        supabase.table("budgets").update({
                            "libelle_groupe": new_lib,
                            "budget": new_budget
                        }).eq("id", row["id"]).execute()
                        st.success("Budget modifié")
                        st.rerun()

                    if delete:
                        supabase.table("budgets").delete().eq("id", row["id"]).execute()
                        st.success("Budget supprimé")
                        st.rerun()