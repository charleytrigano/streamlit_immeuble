import streamlit as st
import pandas as pd

GROUPES_CHARGES = {
    1: "Charges communes générales",
    2: "Charges communes RDC / sous-sols",
    3: "Charges spéciales sous-sols",
    4: "Ascenseurs",
    5: "Monte-voitures",
}

def plan_comptable_ui(supabase):
    st.subheader("📘 Plan comptable – Groupes de charges")

    res = (
        supabase
        .table("plan_comptable")
        .select("compte_8, libelle, groupe_charges")
        .order("compte_8")
        .execute()
    )

    if not res.data:
        st.warning("Plan comptable vide")
        return

    df = pd.DataFrame(res.data)

    for _, row in df.iterrows():
        compte = row["compte_8"]
        libelle = row["libelle"]
        groupe_actuel = row.get("groupe_charges")

        with st.container(border=True):
            st.markdown(f"**{compte} – {libelle}**")

            groupe = st.selectbox(
                "Groupe de charges",
                options=list(GROUPES_CHARGES.keys()),
                format_func=lambda x: f"{x} – {GROUPES_CHARGES[x]}",
                index=list(GROUPES_CHARGES.keys()).index(groupe_actuel)
                if groupe_actuel in GROUPES_CHARGES else 0,
                key=f"select_{compte}"
            )

            if st.button("💾 Enregistrer", key=f"save_{compte}"):
                (
                    supabase
                    .table("plan_comptable")
                    .update({"groupe_charges": groupe})
                    .eq("compte_8", compte)
                    .execute()
                )
                st.success("Groupe de charges mis à jour")