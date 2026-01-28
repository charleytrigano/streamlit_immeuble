import streamlit as st
import pandas as pd


def plan_comptable_ui(supabase):
    st.header("📚 Plan comptable")

    try:
        res = (
            supabase
            .table("plan_comptable")
            .select("compte_8, libelle, groupe_compte, libelle_groupe")
            .order("groupe_compte")
            .order("compte_8")
            .execute()
        )
    except Exception as e:
        st.error("Erreur Supabase (plan_comptable)")
        st.exception(e)
        return

    df = pd.DataFrame(res.data or [])

    if df.empty:
        st.warning("Plan comptable vide")
        return

    st.dataframe(
        df,
        use_container_width=True
    )

    st.info("Le plan comptable est maintenant modifiable via l’UI (RLS OK)")