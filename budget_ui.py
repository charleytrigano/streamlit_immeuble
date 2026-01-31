import streamlit as st
import pandas as pd


def budgets_ui(supabase, annee):
    st.subheader(f"📊 Budget – {annee}")

    res = (
        supabase
        .table("budgets")
        .select("*")
        .eq("annee", annee)
        .order("groupe_compte")
        .execute()
    )

    if not res.data:
        st.info("Aucun budget pour cette année")
        return

    df = pd.DataFrame(res.data)

    st.markdown("### ✏️ Budgets par groupe de charges")

    edited_df = st.data_editor(
        df,
        use_container_width=True,
        num_rows="dynamic",
        key="budgets_editor"
    )

    if not edited_df.equals(df):
        if st.button("💾 Enregistrer les modifications"):
            for _, row in edited_df.iterrows():
                if pd.isna(row.get("id")):
                    # ➕ ajout
                    supabase.table("budgets").insert({
                        "annee": annee,
                        "groupe_compte": row["groupe_compte"],
                        "budget": row["budget"],
                    }).execute()
                else:
                    # ✏️ modification
                    supabase.table("budgets").update({
                        "groupe_compte": row["groupe_compte"],
                        "budget": row["budget"],
                    }).eq("id", row["id"]).execute()

            st.success("✅ Budgets mis à jour")
            st.rerun()
