import streamlit as st
import pandas as pd


def euro(x):
    if x is None:
        return "0,00 €"
    return f"{x:,.2f} €".replace(",", " ").replace(".", ",")


def budget_ui(supabase, annee: int):
    # =============================
    # EN-TÊTE
    # =============================
    st.header("💰 Budget annuel")
    st.caption(f"Année budgétaire : **{annee}**")

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

    st.caption(f"📌 Budgets trouvés : {len(df)} ligne(s)")

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
    k2.metric("📂 Groupes de comptes", nb_groupes)
    k3.metric("📊 Budget moyen / groupe", euro(budget_moyen))

    st.divider()

    # =============================
    # AJOUT D’UN BUDGET
    # =============================
    with st.expander("➕ Ajouter un budget", expanded=False):
        with st.form("add_budget"):
            st.caption(f"Année : **{annee}** (fixée par le filtre global)")

            groupe = st.text_input("Groupe de compte (ex : 606)")
            libelle = st.text_input("Libellé du groupe")
            montant = st.number_input(
                "Montant budget (€)",
                min_value=0.0,
                step=100.0
            )

            submitted = st.form_submit_button("Ajouter ce budget")

            if submitted:
                if not groupe or montant <= 0:
                    st.error("🔴 Groupe de compte et montant sont obligatoires.")
                else:
                    supabase.table("budgets").insert({
                        "annee": annee,              # ✅ année bien enregistrée
                        "groupe_compte": groupe,
                        "libelle_groupe": libelle,
                        "budget": montant
                    }).execute()
                    st.success("✅ Budget ajouté.")
                    st.rerun()

    # =============================
    # TABLEAU + ACTIONS
    # =============================
    if df.empty:
        st.warning("Aucun budget défini pour cette année.")
        return

    st.subheader("📋 Budgets par groupe")

    # On trie par groupe pour une lecture propre
    df = df.sort_values(["groupe_compte", "libelle_groupe"])

    for _, row in df.iterrows():
        with st.container(border=True):
            c0, c1, c2, c3, c4 = st.columns([1, 2, 3, 2, 2])

            # Année (read-only)
            c0.write(f"**{int(row['annee'])}**")

            # Groupe + libellé + montant
            c1.write(f"**{row['groupe_compte']}**")
            c2.write(row.get("libelle_groupe", ""))
            c3.write(euro(row["budget"]))

            # Bouton ouvrir édition
            with c4:
                edit_key = f"edit_{row['id']}"
                if st.button("✏️ Modifier", key=edit_key):
                    st.session_state[edit_key] = True

            # Formulaire d'édition / suppression
            if st.session_state.get(f"edit_{row['id']}"):
                with st.form(f"form_edit_{row['id']}"):
                    st.caption(f"Année : **{int(row['annee'])}**")

                    new_groupe = st.text_input(
                        "Groupe de compte",
                        value=row.get("groupe_compte", "")
                    )
                    new_lib = st.text_input(
                        "Libellé du groupe",
                        value=row.get("libelle_groupe", "")
                    )
                    new_budget = st.number_input(
                        "Budget (€)",
                        value=float(row["budget"]),
                        min_value=0.0,
                        step=100.0
                    )

                    col_save, col_del, col_cancel = st.columns(3)
                    save = col_save.form_submit_button("💾 Enregistrer")
                    delete = col_del.form_submit_button("🗑️ Supprimer")
                    cancel = col_cancel.form_submit_button("❌ Annuler")

                    if save:
                        if not new_groupe or new_budget <= 0:
                            st.error("Groupe de compte et montant sont obligatoires.")
                        else:
                            supabase.table("budgets").update({
                                "groupe_compte": new_groupe,
                                "libelle_groupe": new_lib,
                                "budget": new_budget,
                                # on ne touche pas à annee ici
                            }).eq("id", row["id"]).execute()
                            st.success("✅ Budget modifié.")
                            st.rerun()

                    if delete:
                        supabase.table("budgets") \
                            .delete() \
                            .eq("id", row["id"]) \
                            .execute()
                        st.success("🗑️ Budget supprimé.")
                        st.rerun()

                    if cancel:
                        st.session_state[f"edit_{row['id']}"] = False
                        st.experimental_rerun()