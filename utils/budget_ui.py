import streamlit as st
import pandas as pd


def euro(x):
    if x is None:
        return "0,00 €"
    return f"{x:,.2f} €".replace(",", " ").replace(".", ",")


def budget_ui(supabase, annee):
    st.header("💰 Budget annuel")

    # =========================
    # CHARGEMENT DES BUDGETS
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
    # TABLEAU PAR GROUPE
    # =========================
    st.subheader("📊 Budget par groupe")

    for _, row in df.iterrows():
        col1, col2, col3, col4 = st.columns([2, 4, 2, 2])

        col1.markdown(f"**{row['groupe_compte']}**")
        col2.markdown(row.get("libelle_groupe", "—"))
        col3.markdown(euro(row["budget"]))

        # =========================
        # ACTIONS
        # =========================
        with col4:
            b_mod, b_del = st.columns(2)

            # -------- MODIFIER --------
            if b_mod.button("✏️", key=f"edit_{row['id']}"):
                with st.modal("Modifier le budget"):
                    new_budget = st.number_input(
                        "Montant du budget (€)",
                        min_value=0.0,
                        step=100.0,
                        value=float(row["budget"])
                    )

                    if st.button("💾 Enregistrer"):
                        supabase.table("budgets").update({
                            "budget": new_budget
                        }).eq("id", row["id"]).execute()

                        st.success("Budget mis à jour")
                        st.rerun()

            # -------- SUPPRIMER --------
            if b_del.button("🗑️", key=f"delete_{row['id']}"):
                with st.modal("⚠️ Confirmation de suppression"):
                    st.error(
                        f"Supprimer le budget du groupe **{row['groupe_compte']}** ?\n\n"
                        "Cette action est définitive."
                    )

                    if st.button("❌ Supprimer définitivement"):
                        supabase.table("budgets").delete().eq("id", row["id"]).execute()
                        st.success("Budget supprimé")
                        st.rerun()