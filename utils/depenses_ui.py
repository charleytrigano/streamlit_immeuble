import streamlit as st
import pandas as pd


def depenses_ui(supabase):
    st.title("📄 État des dépenses")
    st.success("Module dépenses chargé correctement ✅")

    # -----------------------------
    # CHARGEMENT DES DONNÉES
    # -----------------------------
    try:
        response = (
            supabase
            .table("depenses")
            .select("*")
            .order("date", desc=True)
            .execute()
        )
        data = response.data or []
        df = pd.DataFrame(data)

    except Exception as e:
        st.error("Erreur de chargement des dépenses")
        st.exception(e)
        return

    if df.empty:
        st.warning("Aucune dépense trouvée")
        return

    # -----------------------------
    # NORMALISATION DES COLONNES
    # -----------------------------
    # Sécurité : on affiche seulement ce qui existe
    colonnes_affichees = [
        "depense_id",
        "annee",
        "compte",
        "poste",
        "fournisseur",
        "date",
        "montant_ttc",
        "type",
        "commentaire",
        "created_st"
    ]

    colonnes_finales = [c for c in colonnes_affichees if c in df.columns]

    # Conversion date si besoin
    if "date" in df.columns:
        df["date"] = pd.to_datetime(df["date"], errors="coerce")

    # -----------------------------
    # KPI
    # -----------------------------
    total = df["montant_ttc"].sum() if "montant_ttc" in df.columns else 0

    c1, c2 = st.columns(2)
    c1.metric("Total dépenses TTC", f"{total:,.2f} €".replace(",", " "))
    c2.metric("Nombre de lignes", len(df))

    st.divider()

    # -----------------------------
    # TABLEAU
    # -----------------------------
    st.dataframe(
        df[colonnes_finales].sort_values(
            "date" if "date" in colonnes_finales else colonnes_finales[0],
            ascending=False
        ),
        use_container_width=True
    )

    # -----------------------------
    # INFO
    # -----------------------------
    st.info(
        "✏️ Ajout / modification / suppression arriveront à l’étape suivante "
        "(base et UI maintenant propres et stables)."
    )