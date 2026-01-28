import streamlit as st
import pandas as pd

# =========================
# UTIL
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
    st.subheader("💰 Budget")

    # =========================
    # CHARGEMENT
    # =========================
    resp = (
        supabase
        .table("budgets")
        .select("*")
        .eq("annee", annee)
        .execute()
    )
    df = pd.DataFrame(resp.data or [])

    plan_resp = (
        supabase
        .table("plan_comptable")
        .select("compte_8, groupe_compte, libelle_groupe")
        .execute()
    )
    df_plan = pd.DataFrame(plan_resp.data or [])

    if df.empty:
        st.warning("Aucun budget pour cette année.")
        df = pd.DataFrame(columns=[
            "id", "annee", "compte", "budget", "groupe_compte", "libelle_groupe"
        ])

    # =========================
    # ENRICHISSEMENT
    # =========================
    df["compte"] = df["compte"].astype(str)
    df["budget"] = pd.to_numeric(df["budget"], errors="coerce").fillna(0)

    if not df_plan.empty:
        df = df.merge(
            df_plan,
            left_on="compte",
            right_on="compte_8",
            how="left",
            suffixes=("", "_plan")
        )

        df["groupe_compte"] = df["groupe_compte"].fillna(df["groupe_compte_plan"])
        df["libelle_groupe"] = df["libelle_groupe"].fillna(df["libelle_groupe_plan"])

    # =========================
    # KPI
    # =========================
    total_budget = df["budget"].sum()

    c1, c2 = st.columns(2)
    c1.metric("Budget total", euro(total_budget))
    c2.metric("Nombre de lignes", len(df))

    # =========================
    # TABLEAU PAR GROUPE
    # =========================
    st.markdown("### 📊 Budget par groupe de comptes")

    grp = (
        df
        .groupby(["groupe_compte", "libelle_groupe"], as_index=False)
        .agg(budget=("budget", "sum"))
        .sort_values("groupe_compte")
    )

    st.dataframe(
        grp.rename(columns={
            "groupe_compte": "Groupe",
            "libelle_groupe": "Libellé groupe",
            "budget": "Budget (€)"
        }),
        use_container_width=True
    )

    # =========================
    # DÉTAIL
    # =========================
    st.markdown("### 📋 Détail du budget")

    st.dataframe(
        df[[
            "compte",
            "groupe_compte",
            "libelle_groupe",
            "budget"
        ]].sort_values("compte"),
        use_container_width=True
    )

    # =========================
    # AJOUT
    # =========================
    st.markdown("### ➕ Ajouter une ligne de budget")

    with st.form("add_budget"):
        b_compte = st.text_input("Compte (8 chiffres)")
        b_groupe = st.text_input("Groupe de compte")
        b_libelle = st.text_input("Libellé du groupe")
        b_montant = st.number_input("Montant du budget", step=100.0)

        submit = st.form_submit_button("Ajouter")

        if submit:
            supabase.table("budgets").insert({
                "annee": annee,
                "compte": b_compte,
                "groupe_compte": b_groupe,
                "libelle_groupe": b_libelle,
                "budget": b_montant
            }).execute()

            st.success("Budget ajouté")
            st.rerun()

    # =========================
    # MODIFICATION
    # =========================
    st.markdown("### ✏️ Modifier une ligne")

    if not df.empty:
        choix = {
            f"{row['compte']} | {euro(row['budget'])}": row["id"]
            for _, row in df.iterrows()
        }

        sel = st.selectbox("Sélection", list(choix.keys()))
        row = df[df["id"] == choix[sel]].iloc[0]

        with st.form("edit_budget"):
            e_budget = st.number_input(
                "Montant",
                value=float(row["budget"]),
                step=100.0
            )

            submit_edit = st.form_submit_button("Enregistrer")

            if submit_edit:
                supabase.table("budgets").update({
                    "budget": e_budget
                }).eq("id", row["id"]).execute()

                st.success("Budget modifié")
                st.rerun()

    # =========================
    # SUPPRESSION
    # =========================
    st.markdown("### 🗑️ Supprimer une ligne")

    if not df.empty:
        sel_del = st.selectbox(
            "Ligne à supprimer",
            list(choix.keys()),
            key="del_budget"
        )

        if st.button("Supprimer"):
            supabase.table("budgets").delete().eq(
                "id", choix[sel_del]
            ).execute()

            st.success("Budget supprimé")
            st.rerun()