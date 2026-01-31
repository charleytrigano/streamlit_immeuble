import streamlit as st
import pandas as pd


def appels_fonds_trimestre_ui(supabase, annee: int):
    st.subheader(f"📢 Appels de fonds par trimestre – Année {annee}")

    # ============================================================
    # 1) Récupération des données de répartition par lot
    #    ⚠️ Vérifie le nom de la vue / table : ici "repartition_par_lot"
    # ============================================================
    res = (
        supabase
        .table("repartition_par_lot")
        .select("*")
        .eq("annee", annee)
        .order("proprietaire")  # ou "lot" selon ce que tu préfères
        .execute()
    )

    if not res.data:
        st.warning("Aucune répartition trouvée pour cette année.")
        return

    df = pd.DataFrame(res.data)

    # ============================================================
    # 2) Harmonisation des types numériques
    #    ⚠️ Adapte la liste des colonnes à ton schéma réel
    # ============================================================
    numeric_cols = [
        "charges_communes_generales",
        "charges_communes_rdc_ss",
        "charges_speciales_ss",
        "charges_garages_parkings",
        "ascenseurs",
        "monte_voitures",
        "total_charges",
        "loi_alur",
        "total_a_appeler",
        "appel_trimestriel",
    ]

    for col in numeric_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")
        else:
            # Si une colonne manque, on la crée vide pour éviter les plantages
            df[col] = 0.0

    # ============================================================
    # 3) Calcul du total par colonne (ligne "TOTAL IMMEUBLE")
    # ============================================================
    totals = df[numeric_cols].sum().round(2)

    total_row = {col: totals[col] for col in numeric_cols}
    # Colonnes d'identification – à adapter selon ton schéma
    if "proprietaire" in df.columns:
        total_row["proprietaire"] = "TOTAL IMMEUBLE"
    if "lot" in df.columns:
        total_row["lot"] = ""
    if "annee" in df.columns:
        total_row["annee"] = annee

    df_total = pd.concat([df, pd.DataFrame([total_row])], ignore_index=True)

    # ============================================================
    # 4) Contrôle global vs budget (table budgets)
    # ============================================================
    # Budget annuel théorique d'après la table "budgets"
    res_budget = (
        supabase
        .table("budgets")
        .select("budget")
        .eq("annee", annee)
        .execute()
    )

    budget_annuel = 0.0
    if res_budget.data:
        df_bud = pd.DataFrame(res_budget.data)
        df_bud["budget"] = pd.to_numeric(df_bud["budget"], errors="coerce")
        budget_annuel = float(df_bud["budget"].sum())

    # Total annuel calculé par la répartition (somme des appels trimestriels × 4)
    total_trimestriel = float(totals["appel_trimestriel"])
    total_annuel_calcule = round(total_trimestriel * 4, 2)

    # Carte de contrôle
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("💰 Budget annuel (table budgets)", f"{budget_annuel:,.2f} €".replace(",", " ").replace(".", ","))
    with col2:
        st.metric("📊 Total annuel calculé (répartition)", f"{total_annuel_calcule:,.2f} €".replace(",", " ").replace(".", ","))
    with col3:
        diff = round(total_annuel_calcule - budget_annuel, 2)
        st.metric("Écart", f"{diff:,.2f} €".replace(",", " ").replace(".", ","))

    if budget_annuel > 0 and abs(total_annuel_calcule - budget_annuel) < 0.01:
        st.success("✅ Contrôle OK : la répartition correspond au budget annuel.")
    else:
        st.error(
            "❌ Contrôle KO : la répartition ne correspond pas au budget annuel.\n\n"
            "👉 Vérifie la table **budgets** (montants, doublons, année, etc.)."
        )

    st.markdown("### 📋 Détail par propriétaire / lot")

    # ============================================================
    # 5) Affichage du tableau avec ligne de total
    # ============================================================
    # On formate juste pour l'affichage (sans toucher au df de calcul si tu veux le réutiliser)
    df_aff = df_total.copy()

    # Optionnel : formater les nombres en chaîne "X XXX,YY €" pour l'affichage
    def fmt_euro(x):
        if pd.isna(x):
            return ""
        return f"{x:,.2f} €".replace(",", " ").replace(".", ",")

    for col in numeric_cols:
        df_aff[col] = df_aff[col].apply(fmt_euro)

    st.dataframe(
        df_aff,
        use_container_width=True,
        hide_index=True,
    )
