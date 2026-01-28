import streamlit as st
import pandas as pd


def euro(x):
    if x is None:
        return "0,00 €"
    return f"{x:,.2f} €".replace(",", " ").replace(".", ",")


def budget_ui(supabase, annee):
    st.header("💰 Budget annuel")

    # =========================
    # LECTURE DES DONNÉES
    # =========================
    res = (
        supabase
        .table("budgets")
        .select("*")
        .eq("annee", annee)
        .order("groupe_compte")
        .execute()
    )

    data = res.data or []

    st.caption(f"📌 Budgets trouvés : {len(data)} lignes")

    if not data:
        st.warning("Aucun budget défini pour cette année.")
        return

    df = pd.DataFrame(data)

    # =========================
    # KPI
    # =========================
    total_budget = df["budget"].sum()

    c1, c2 = st.columns(2)
    c1.metric("Budget total", euro(total_budget))
    c2.metric("Nombre de groupes", len(df))

    st.divider()

    # =========================
    # TABLEAU
    # =========================
    st.subheader("📊 Budget par groupe")

    # Init session state suppression
    if "confirm_delete_budget" not in st.session_state:
        st.session_state.confirm_delete_budget = None

    for _, row in df.iterrows():
        col1, col2, col3, col4 = st.columns([2, 4, 2, 2])

        col1.markdown(f"**{row['groupe_compte']}**")
        col2.markdown(row.get("libelle_groupe", "—"))
        col3.markdown(euro(row["budget"]))

        with col4:
            b1, b2 = st.columns(2)

            # =========================
            # MODIFIER
            # =========================
            if b1.button("✏️", key=f"edit_{row['id']}"):
                st.session_state[f"edit_{row['id']}"] = True

            # =========================
            # SUPPRIMER (ÉTAPE 1)
            # =========================
            if b2.button("🗑️", key=f"ask_delete_{row['id']}"):
                st.session_state.confirm_delete_budget = row["id"]

        # =========================
        # FORMULAIRE MODIFICATION
        # =========================
        if st.session_state.get(f"edit_{row['id']}"):
            with st.form(f"form_edit_{row['id']}"):
                new_budget = st.number_input(
                    "Montant du budget (€)",
                    min_value=0.0,
                    step=100.0,
                    value=float(row["budget"])
                )

                col_ok, col_cancel = st.columns(2)
                save = col_ok.form_submit_button("💾 Enregistrer")
                cancel = col_cancel.form_submit_button("❌ Annuler")

                if save:
                    supabase.table("budgets").update({
                        "budget": new_budget
                    }).eq("id", row["id"]).execute()

                    st.success("Budget mis à jour")
                    st.session_state.pop(f"edit_{row['id']}")
                    st.rerun()

                if cancel:
                    st.session_state.pop(f"edit_{row['id']}")
                    st.rerun()

        # =========================
        # CONFIRMATION SUPPRESSION
        # =========================
        if st.session_state.confirm_delete_budget == row["id"]:
            st.error(
                f"⚠️ Supprimer définitivement le budget du groupe "
                f"**{row['groupe_compte']}** ?"
            )

            cdel1, cdel2 = st.columns(2)
            if cdel1.button("❌ Oui, supprimer", key=f"confirm_del_{row['id']}"):
                supabase.table("budgets").delete().eq("id", row["id"]).execute()
                st.session_state.confirm_delete_budget = None
                st.success("Budget supprimé")
                st.rerun()

            if cdel2.button("↩️ Annuler", key=f"cancel_del_{row['id']}"):
                st.session_state.confirm_delete_budget = None
                st.rerun()