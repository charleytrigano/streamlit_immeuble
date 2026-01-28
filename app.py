import streamlit as st
import pandas as pd
from supabase import create_client

# ---------------- CONFIG ----------------
st.set_page_config(page_title="Pilotage des charges", layout="wide")

SUPABASE_URL = st.secrets["SUPABASE_URL"]
SUPABASE_ANON_KEY = st.secrets["SUPABASE_ANON_KEY"]

supabase = create_client(SUPABASE_URL, SUPABASE_ANON_KEY)

# ---------------- HELPERS ----------------
def load_table(name):
    res = supabase.table(name).select("*").execute()
    return pd.DataFrame(res.data) if res.data else pd.DataFrame()

def euro(x):
    return f"{x:,.2f} €".replace(",", " ").replace(".", ",")

# ---------------- MAIN ----------------
def main():
    st.title("📊 Pilotage des charges – Budget vs Réel")

    # ---------- LOAD DATA ----------
    df_dep = load_table("depenses")
    df_bud = load_table("budgets")

    if df_dep.empty:
        st.warning("Aucune dépense enregistrée")
        return

    # ---------- FILTRES ----------
    annee = st.selectbox(
        "Année",
        sorted(df_dep["annee"].dropna().unique(), reverse=True)
    )

    dep_y = df_dep[df_dep["annee"] == annee].copy()
    bud_y = df_bud[df_bud["annee"] == annee].copy() if not df_bud.empty else pd.DataFrame()

    # ---------- NORMALISATION ----------
    dep_y["montant_ttc"] = pd.to_numeric(dep_y["montant_ttc"], errors="coerce").fillna(0)

    # sens comptable sécurisé
    sens_valides = ["Charge", "Avoir", "Remboursement"]
    dep_y["sens"] = dep_y["sens"].where(dep_y["sens"].isin(sens_valides), "Charge")

    # ---------- KPI ----------
    total_charges = dep_y[dep_y["sens"] == "Charge"]["montant_ttc"].sum()
    total_avoirs = dep_y[dep_y["sens"] == "Avoir"]["montant_ttc"].sum()
    total_remb = dep_y[dep_y["sens"] == "Remboursement"]["montant_ttc"].sum()

    net_reel = total_charges - total_avoirs - total_remb
    budget_total = bud_y["budget"].sum() if not bud_y.empty else 0
    ecart = net_reel - budget_total

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Charges réelles", euro(net_reel))
    c2.metric("Budget", euro(budget_total))
    c3.metric("Écart", euro(ecart), delta_color="inverse")
    c4.metric("Avoirs", euro(total_avoirs))

    st.divider()

    # ---------- DEPENSES ----------
    st.subheader("📋 Dépenses")

    dep_display_cols = [
        "depense_id",
        "date",
        "compte",
        "poste",
        "fournisseur",
        "type",
        "sens",
        "montant_ttc",
        "commentaire"
    ]

    dep_disp = dep_y[[c for c in dep_display_cols if c in dep_y.columns]].sort_values("date")

    st.dataframe(
        dep_disp,
        use_container_width=True,
        column_config={
            "montant_ttc": st.column_config.NumberColumn("Montant TTC", format="%.2f €")
        }
    )

    st.divider()

    # ---------- BUDGET PAR GROUPE ----------
    st.subheader("📊 Budget par groupe")

    if bud_y.empty:
        st.info("Aucun budget pour cette année")
    else:
        bud_grp = (
            bud_y
            .groupby(["groupe_compte", "libelle_groupe"], as_index=False)["budget"]
            .sum()
            .sort_values("groupe_compte")
        )

        st.dataframe(
            bud_grp,
            use_container_width=True,
            column_config={
                "budget": st.column_config.NumberColumn("Budget", format="%.2f €")
            }
        )

    # ---------- AJOUT DEPENSE ----------
    st.divider()
    st.subheader("➕ Ajouter une dépense")

    with st.form("add_depense"):
        col1, col2, col3 = st.columns(3)

        with col1:
            date = st.date_input("Date")
            compte = st.text_input("Compte")
            poste = st.text_input("Poste")

        with col2:
            fournisseur = st.text_input("Fournisseur")
            type_libre = st.text_input("Type (libre)")
            sens = st.selectbox("Sens comptable", sens_valides)

        with col3:
            montant = st.number_input("Montant TTC", min_value=0.0, step=0.01)
            commentaire = st.text_input("Commentaire")

        submit = st.form_submit_button("Enregistrer")

        if submit:
            supabase.table("depenses").insert({
                "annee": annee,
                "date": str(date),
                "compte": compte,
                "poste": poste,
                "fournisseur": fournisseur,
                "type": type_libre,
                "sens": sens,
                "montant_ttc": montant,
                "commentaire": commentaire
            }).execute()

            st.success("Dépense ajoutée")
            st.rerun()

# ---------------- RUN ----------------
if __name__ == "__main__":
    main()