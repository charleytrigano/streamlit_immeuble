import streamlit as st
import pandas as pd
from supabase import create_client

# =========================
# CONFIG
# =========================
BASE_TANTIEMES = 10_000

st.set_page_config(
    page_title="Pilotage des charges",
    layout="wide"
)

# =========================
# SUPABASE
# =========================
@st.cache_resource
def get_supabase():
    return create_client(
        st.secrets["SUPABASE_URL"],
        st.secrets["SUPABASE_ANON_KEY"]
    )

# =========================
# FORMAT €
# =========================
def euro(v):
    return f"{v:,.2f} €".replace(",", " ").replace(".", ",")

# =========================
# MAIN
# =========================
def main():
    supabase = get_supabase()

    # =========================
    # SIDEBAR
    # =========================
    st.sidebar.title("Navigation")

    page = st.sidebar.radio(
        "Aller à",
        [
            "📄 État des dépenses",
            "💰 Budget",
            "📊 Budget vs Réel",
            "📈 Statistiques",
            "✅ Contrôle de répartition",
        ]
    )

    # =========================
    # 📄 ÉTAT DES DÉPENSES
    # =========================
    if page == "📄 État des dépenses":
        st.title("📄 État des dépenses")

        annee = st.selectbox("Année", [2023, 2024, 2025, 2026], index=2)

        resp = (
            supabase
            .table("depenses")
            .select("*")
            .eq("annee", annee)
            .execute()
        )

        df = pd.DataFrame(resp.data)

        if df.empty:
            st.info("Aucune dépense.")
        else:
            df["facture"] = df["facture_url"].apply(
                lambda x: f"[📄 Ouvrir]({x})" if x else ""
            )

            st.dataframe(
                df[[
                    "date",
                    "compte",
                    "poste",
                    "fournisseur",
                    "montant_ttc",
                    "commentaire",
                    "facture"
                ]],
                use_container_width=True
            )

        # -------------------------
        # AJOUT
        # -------------------------
        with st.expander("➕ Ajouter une dépense"):
            with st.form("add_depense"):
                date = st.date_input("Date")
                compte = st.text_input("Compte")
                poste = st.text_input("Poste")
                fournisseur = st.text_input("Fournisseur")
                montant = st.number_input("Montant TTC", value=0.0)
                commentaire = st.text_input("Commentaire")
                facture_url = st.text_input("Lien facture (optionnel)")

                if st.form_submit_button("Enregistrer"):
                    supabase.table("depenses").insert({
                        "date": str(date),
                        "annee": date.year,
                        "compte": compte,
                        "poste": poste,
                        "fournisseur": fournisseur,
                        "montant_ttc": montant,
                        "commentaire": commentaire,
                        "facture_url": facture_url
                    }).execute()
                    st.success("Dépense ajoutée")
                    st.rerun()

    # =========================
    # 💰 BUDGET
    # =========================
    elif page == "💰 Budget":
        st.title("💰 Budget")

        annee = st.selectbox("Année", [2023, 2024, 2025, 2026], index=2)

        bud = (
            supabase
            .table("budgets")
            .select("*")
            .eq("annee", annee)
            .execute()
        )

        df = pd.DataFrame(bud.data)

        if not df.empty:
            st.metric("Budget total", euro(df["montant"].sum()))
            st.dataframe(df[["compte", "montant"]], use_container_width=True)
        else:
            st.info("Aucun budget")

    # =========================
    # 📊 BUDGET VS RÉEL
    # =========================
    elif page == "📊 Budget vs Réel":
        st.title("📊 Budget vs Réel")

        annee = st.selectbox("Année", [2023, 2024, 2025, 2026], index=2)

        dep = pd.DataFrame(
            supabase.table("depenses").select("compte, montant_ttc").eq("annee", annee).execute().data
        )
        bud = pd.DataFrame(
            supabase.table("budgets").select("compte, montant").eq("annee", annee).execute().data
        )

        if dep.empty or bud.empty:
            st.warning("Données manquantes")
            return

        dep_g = dep.groupby("compte", as_index=False)["montant_ttc"].sum()
        df = bud.merge(dep_g, on="compte", how="left").fillna(0)

        df["écart"] = df["montant_ttc"] - df["montant"]

        st.dataframe(
            df.rename(columns={
                "montant": "Budget",
                "montant_ttc": "Réel"
            }),
            use_container_width=True
        )

    # =========================
    # 📈 STATISTIQUES
    # =========================
    elif page == "📈 Statistiques":
        st.title("📈 Statistiques")

        dep = pd.DataFrame(
            supabase.table("depenses").select("poste, montant_ttc").execute().data
        )

        if dep.empty:
            st.info("Pas de données")
            return

        st.dataframe(
            dep.groupby("poste", as_index=False)
            .agg(total=("montant_ttc", "sum"))
            .sort_values("total", ascending=False),
            use_container_width=True
        )

    # =========================
    # ✅ CONTRÔLE RÉPARTITION
    # =========================
    elif page == "✅ Contrôle de répartition":
        st.title("✅ Contrôle de répartition")

        dep = pd.DataFrame(
            supabase.table("depenses").select("id, montant_ttc").execute().data
        )
        rep = pd.DataFrame(
            supabase.table("repartition_depenses").select("depense_id, quote_part").execute().data
        )

        if dep.empty or rep.empty:
            st.warning("Données manquantes")
            return

        rep_sum = (
            rep.groupby("depense_id", as_index=False)
            .agg(reparti=("quote_part", "sum"))
        )

        df = dep.merge(rep_sum, left_on="id", right_on="depense_id", how="left").fillna(0)
        df["écart"] = df["montant_ttc"] - (df["montant_ttc"] * df["reparti"] / BASE_TANTIEMES)

        anomalies = df[abs(df["écart"]) > 0.01]

        if anomalies.empty:
            st.success("Toutes les dépenses sont correctement réparties")
        else:
            st.error("Anomalies détectées")
            st.dataframe(anomalies, use_container_width=True)


# =========================
# RUN
# =========================
if __name__ == "__main__":
    main()