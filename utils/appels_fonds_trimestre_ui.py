import streamlit as st
import pandas as pd
from postgrest.exceptions import APIError


def appels_fonds_trimestre_ui(supabase, annee: int):
    st.subheader(f"📢 Appels de fonds trimestriels – {annee}")

    try:
        res = (
            supabase
            # ⚠️ METS ICI LE NOM EXACT QUE TU UTILISES
            .table("repartition_par_lot_controle")
            .select("*")
            .eq("annee", annee)
            .execute()
        )

    except APIError as e:
        st.error("❌ Erreur Supabase lors de la lecture des appels de fonds")
        st.code(str(e), language="text")
        st.info(
            "Causes probables :\n"
            "- vue non accessible avec anon_key\n"
            "- RLS actif sur table source\n"
            "- mauvais nom de vue\n"
        )
        return

    if not res.data:
        st.warning("Aucune donnée retournée.")
        return

    df = pd.DataFrame(res.data)

    st.success(f"{len(df)} lignes chargées")
    st.dataframe(df, use_container_width=True)