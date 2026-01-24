import streamlit as st
import pandas as pd


def repartition_lots_ui(supabase):
    st.title("🏠 Répartition des dépenses par lots")

    # ----------------------------------------
    # 1) Sélection de l'année
    # ----------------------------------------
    # Récupérer la liste des années présentes dans depenses
    annees_resp = (
        supabase
        .table("depenses")
        .select("annee")
        .order("annee")
        .execute()
    )

    if not annees_resp.data:
        st.warning("Aucune dépense trouvée dans la base.")
        return

    annees = sorted({row["annee"] for row in annees_resp.data})
    annee = st.selectbox("Année", annees, index=len(annees) - 1)

    # ----------------------------------------
    # 2) Chargement des données nécessaires
    #    - depenses de l'année
    #    - repartition_depenses liées
    #    - lots
    # ----------------------------------------
    dep_resp = (
        supabase
        .table("depenses")
        .select(
            "id, annee, compte, poste, fournisseur, date, montant_ttc, type"
        )
        .eq("annee", annee)
        .execute()
    )

    if not dep_resp.data:
        st.warning(f"Aucune dépense pour l'année {annee}.")
        return

    df_dep = pd.DataFrame(dep_resp.data)

    # Liste des id de dépenses de l'année
    dep_ids = df_dep["id"].tolist()

    rep_resp = (
        supabase
        .table("repartition_depenses")
        .select("depense_id, lot_id, quote_part")
        .in_("depense_id", dep_ids)
        .execute()
    )

    if not rep_resp.data:
        st.warning(
            "Aucune répartition trouvée pour ces dépenses.\n"
            "Vérifie que la table 'repartition_depenses' est bien remplie."
        )
        return

    df_rep = pd.DataFrame(rep_resp.data)

    lots_resp = (
        supabase
        .table("lots")
        .select("id, lot, tantiemes, batiment, etage, usage, description")
        .execute()
    )

    if not lots_resp.data:
        st.warning("La table 'lots' est vide : impossible d'afficher la répartition.")
        return

    df_lots = pd.DataFrame(lots_resp.data)

    # ----------------------------------------
    # 3) Jointure : repartition + depenses + lots
    # ----------------------------------------
    # Jointure répartition ↔ dépenses
    df = df_rep.merge(
        df_dep,
        left_on="depense_id",
        right_on="id",
        how="left",
        suffixes=("", "_dep"),
    )

    # Jointure avec lots
    df = df.merge(
        df_lots,
        left_on="lot_id",
        right_on="id",
        how="left",
        suffixes=("", "_lot"),
    )

    # Nettoyage des colonnes techniques
    df = df.drop(columns=[col for col in ["id", "id_lot"] if col in df.columns])

    # Sécurité typage
    df["quote_part"] = df["quote_part"].astype(float)
    if "tantiemes" in df.columns:
        df["tantiemes"] = pd.to_numeric(df["tantiemes"], errors="coerce")

    # ----------------------------------------
    # 4) Filtres interactifs
    # ----------------------------------------
    st.subheader("Filtres")

    col_f1, col_f2, col_f3 = st.columns(3)

    lots_options = sorted(df["lot"].dropna().unique().tolist())
    selected_lots = col_f1.multiselect("Lots", lots_options)

    batiments_options = sorted(df["batiment"].dropna().unique().tolist())
    selected_batiments = col_f2.multiselect("Bâtiments", batiments_options)

    usages_options = sorted(df["usage"].dropna().unique().tolist())
    selected_usages = col_f3.multiselect("Usages", usages_options)

    # Application des filtres
    mask = pd.Series(True, index=df.index)

    if selected_lots:
        mask &= df["lot"].isin(selected_lots)

    if selected_batiments:
        mask &= df["batiment"].isin(selected_batiments)

    if selected_usages:
        mask &= df["usage"].isin(selected_usages)

    df_f = df[mask].copy()

    if df_f.empty:
        st.warning("Aucune ligne ne correspond aux filtres sélectionnés.")
        return

    # ----------------------------------------
    # 5) KPI globaux
    # ----------------------------------------
    total_reparti = df_f["quote_part"].sum()
    nb_lots = df_f["lot_id"].nunique()
    nb_depenses = df_f["depense_id"].nunique()
    moyenne_par_lot = total_reparti / nb_lots if nb_lots > 0 else 0

    col1, col2, col3, col4 = st.columns(4)

    col1.metric("Montant réparti total (€)", f"{total_reparti:,.2f}")
    col2.metric("Nombre de lots concernés", int(nb_lots))
    col3.metric("Nombre de dépenses", int(nb_depenses))
    col4.metric("Moyenne par lot (€)", f"{moyenne_par_lot:,.2f}")

    # ----------------------------------------
    # 6) Tableau agrégé par lot
    # ----------------------------------------
    st.subheader("Synthèse par lot")

    group_cols = ["lot_id", "lot", "batiment", "etage", "usage", "tantiemes"]

    df_lot = (
        df_f.groupby(group_cols, as_index=False)
        .agg(
            montant_reparti=("quote_part", "sum"),
            nb_depenses=("depense_id", "nunique"),
        )
    )

    df_lot["montant_reparti"] = df_lot["montant_reparti"].round(2)

    df_lot = df_lot.rename(
        columns={
            "lot": "Lot",
            "batiment": "Bâtiment",
            "etage": "Étage",
            "usage": "Usage",
            "tantiemes": "Tantièmes",
            "montant_reparti": "Montant réparti (€)",
            "nb_depenses": "Nb de dépenses",
        }
    )

    st.dataframe(
        df_lot.sort_values(["Bâtiment", "Lot"]),
        use_container_width=True,
    )

    # ----------------------------------------
    # 7) Détail des lignes (optionnel)
    # ----------------------------------------
    with st.expander("Voir le détail des dépenses par lot"):
        df_detail = df_f.copy()
        df_detail = df_detail.rename(
            columns={
                "lot": "Lot",
                "batiment": "Bâtiment",
                "etage": "Étage",
                "usage": "Usage",
                "tantiemes": "Tantièmes",
                "quote_part": "Quote-part (€)",
                "compte": "Compte",
                "poste": "Poste",
                "fournisseur": "Fournisseur",
                "date": "Date",
                "montant_ttc": "Montant TTC dépense (€)",
                "type": "Type de dépense",
            }
        )
        st.dataframe(
            df_detail[
                [
                    "Lot",
                    "Bâtiment",
                    "Étage",
                    "Usage",
                    "Tantièmes",
                    "Date",
                    "Compte",
                    "Poste",
                    "Fournisseur",
                    "Montant TTC dépense (€)",
                    "Quote-part (€)",
                    "Type de dépense",
                ]
            ].sort_values(["Lot", "Date"]),
            use_container_width=True,
        )
