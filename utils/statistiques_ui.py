import streamlit as st
import pandas as pd


def statistiques_ui(supabase):
    st.title("📈 Statistiques – DEBUG")

    resp = (
        supabase
        .table("depenses")
        .select("*")
        .execute()
    )

    if not resp.data:
        st.error("Aucune ligne dans la table depenses")
        return

    df = pd.DataFrame(resp.data)

    st.success(f"Lignes chargées depuis Supabase : {len(df)}")
    st.write("Colonnes disponibles :", list(df.columns))

    st.dataframe(df.head(20), use_container_width=True)