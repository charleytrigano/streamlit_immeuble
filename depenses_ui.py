import streamlit as st
import pandas as pd


def euro(x: float) -> str:
    """Formate un nombre en euros, style français."""
    return f"{x:,.2f} €".replace(",", " ").replace(".", ",")


# Mapping des groupes de charges (1–6)
GROUPE_CHARGES_LABELS = {
    1: "1 – Charges communes générales",
    2: "2 – Charges spéciales RDC / sous-sols",
    3: "3 – Charges spéciales sous-sols",
    4: "4 – Ascenseurs",
    5: "5 – Monte-voiture",
    6: "6 – Garages / parkings",
}


def depenses_ui(supabase):
    st.header("📄 Dépenses par groupe de charges")

    # =========================
    # Sélecteur d'année
    # =========================
    annee = st.selectbox(
        "Année",
        options=[2023, 2024, 2025, 2026],
        index=2,
        key="dep_annee",
    )

    # =========================
    # Chargement DEPENSES
    # =========================
    res_dep = (
        supabase
        .table("depenses")
        .select(
            "depense_id, annee, date, compte, poste, fournisseur, montant_ttc, type, commentaire"
        )
        .eq("annee", annee)
        .execute()
    )

    if not res_dep.data:
        st.info(f"Aucune dépense trouvée pour {annee}.")
        return

    df_dep = pd.DataFrame(res_dep.data)

    # Sécurité typage
    df_dep["montant_ttc"] = pd.to_numeric(df_dep["montant_ttc"], errors="coerce").fillna(0)
    df_dep["compte"] = df_dep["compte"].astype(str)

    # =========================
    # Chargement PLAN COMPTABLE
    # =========================
    res_plan = (
        supabase
        .table("plan_comptable")
        .select("compte_8, libelle, groupe_charges")
        .execute()
    )

    if not res_plan.data:
        st.error("⚠️ Plan comptable vide : impossible de regrouper par groupe de charges.")
        return

    df_plan = pd.DataFrame(res_plan.data)
    df_plan["compte_8"] = df_plan["compte_8"].astype(str)
    df_plan["groupe_charges"] = pd.to_numeric(
        df_plan["groupe_charges"], errors="coerce"
    )

    # =========================
    # Jointure DEPENSES ↔ PLAN COMPTABLE
    # =========================
    df = df_dep.merge(
        df_plan,
        left_on="compte",
        right_on="compte_8",
        how="left"
    )

    # Libellé groupe de charges
    def label_groupe(val):
        try:
            g = int(val)
        except (TypeError, ValueError):
            return "Non défini"
        return GROUPE_CHARGES_LABELS.get(g, f"{g} – Non défini")

    df["groupe_charges_label"] = df["groupe_charges"].apply(label_groupe)

    # =========================
    # Filtres complémentaires
    # =========================
    with st.expander("🔎 Filtres détaillés", expanded=False):
        col_f1, col_f2, col_f3 = st.columns(3)

        # Filtre groupe de charges
        groupes_dispo = sorted(df["groupe_charges_label"].dropna().unique().tolist())
        filtre_groupes = col_f1.multiselect(
            "Groupes de charges",
            options=groupes_dispo,
            default=groupes_dispo,
        )

        # Filtre comptes
        comptes_dispo = sorted(df["compte"].dropna().unique().tolist())
        filtre_comptes = col_f2.multiselect(
            "Comptes",
            options=comptes_dispo,
            default=comptes_dispo,
        )

        # Filtre fournisseurs
        fournisseurs_dispo = sorted(df["fournisseur"].dropna().unique().tolist())
        filtre_fournisseurs = col_f3.multiselect(
            "Fournisseurs",
            options=fournisseurs_dispo,
            default=fournisseurs_dispo,
        )

    # Application des filtres
    df_f = df[
        df["groupe_charges_label"].isin(filtre_groupes)
        & df["compte"].isin(filtre_comptes)
        & df["fournisseur"].isin(filtre_fournisseurs)
    ].copy()

    if df_f.empty:
        st.warning("Aucune dépense ne correspond aux filtres.")
        return

    # =========================
    # KPI globaux
    # =========================
    total = df_f["montant_ttc"].sum()
    nb_lignes = len(df_f)
    moyenne = total / nb_lignes if nb_lignes else 0

    c1, c2, c3 = st.columns(3)
    c1.metric("Total des dépenses", euro(total))
    c2.metric("Nombre de lignes", f"{nb_lignes}")
    c3.metric("Dépense moyenne", euro(moyenne))

    # =========================
    # Tableau AGRÉGÉ par groupe de charges
    # =========================
    st.subheader("📊 Dépenses par groupe de charges")

    df_grp = (
        df_f
        .groupby(["groupe_charges", "groupe_charges_label"], as_index=False)
        .agg(montant_total=("montant_ttc", "sum"))
        .sort_values("groupe_charges")
    )

    df_grp["montant_total"] = df_grp["montant_total"].round(2)

    st.dataframe(
        df_grp.rename(columns={
            "groupe_charges_label": "Groupe de charges",
            "montant_total": "Montant total (€)",
        })[["groupe_charges", "Groupe de charges", "Montant total (€)"]],
        use_container_width=True,
    )

    # =========================
    # Détail des dépenses (lignes)
    # =========================
    st.subheader("📋 Détail des dépenses (filtrées)")

    df_detail = df_f[[
        "date",
        "compte",
        "poste",
        "fournisseur",
        "montant_ttc",
        "groupe_charges_label",
        "commentaire",
    ]].sort_values("date")

    df_detail["montant_ttc"] = df_detail["montant_ttc"].round(2)

    st.dataframe(
        df_detail.rename(columns={
            "date": "Date",
            "compte": "Compte",
            "poste": "Poste",
            "fournisseur": "Fournisseur",
            "montant_ttc": "Montant TTC (€)",
            "groupe_charges_label": "Groupe de charges",
            "commentaire": "Commentaire",
        }),
        use_container_width=True,
    )