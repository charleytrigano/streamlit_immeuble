import streamlit as st
import pandas as pd


def euro(x):
    try:
        return f"{float(x):,.2f} €".replace(",", " ").replace(".", ",")
    except Exception:
        return "0,00 €"


def depenses_ui(supabase, annee):
    st.header(f"📄 Dépenses – {annee}")

    # ======================================================
    # CHARGEMENT DES DÉPENSES
    # ======================================================
    dep_resp = (
        supabase
        .table("depenses")
        .select(
            "depense_id, annee, compte, poste, fournisseur, date, montant_ttc, lot_id, commentaire"
        )
        .eq("annee", annee)
        .execute()
    )

    if not dep_resp.data:
        st.info("Aucune dépense pour cette année.")
        return

    df_dep = pd.DataFrame(dep_resp.data)

    # ======================================================
    # CHARGEMENT PLAN COMPTABLE (GROUPES DE CHARGES)
    # ======================================================
    plan_resp = (
        supabase
        .table("plan_comptable")
        .select("compte_8, groupe_charges")
        .execute()
    )

    df_plan = pd.DataFrame(plan_resp.data)

    # ======================================================
    # JOINTURE
    # ======================================================
    df = df_dep.merge(
        df_plan,
        how="left",
        left_on="compte",
        right_on="compte_8"
    )

    # ======================================================
    # NORMALISATION GROUPE_CHARGES (POINT CRITIQUE)
    # ======================================================
    df["groupe_charges"] = (
        df["groupe_charges"]
        .fillna(0)              # NULL → 0
        .astype(int)            # sécurité
        .astype(str)            # TRI SAFE
    )

    # ======================================================
    # FILTRES
    # ======================================================
    st.subheader("🔎 Filtres")

    col1, col2, col3 = st.columns(3)

    with col1:
        groupes = ["Tous"] + sorted(df["groupe_charges"].unique().tolist())
        groupe_sel = st.selectbox("Groupe de charges", groupes)

    with col2:
        fournisseurs = ["Tous"] + sorted(
            df["fournisseur"].dropna().astype(str).unique().tolist()
        )
        fournisseur_sel = st.selectbox("Fournisseur", fournisseurs)

    with col3:
        postes = ["Tous"] + sorted(
            df["poste"].dropna().astype(str).unique().tolist()
        )
        poste_sel = st.selectbox("Poste", postes)

    df_f = df.copy()

    if groupe_sel != "Tous":
        df_f = df_f[df_f["groupe_charges"] == groupe_sel]

    if fournisseur_sel != "Tous":
        df_f = df_f[df_f["fournisseur"] == fournisseur_sel]

    if poste_sel != "Tous":
        df_f = df_f[df_f["poste"] == poste_sel]

    # ======================================================
    # KPI
    # ======================================================
    total = df_f["montant_ttc"].sum()
    nb = len(df_f)
    moyenne = total / nb if nb else 0

    c1, c2, c3 = st.columns(3)
    c1.metric("Total dépenses", euro(total))
    c2.metric("Nombre de lignes", nb)
    c3.metric("Dépense moyenne", euro(moyenne))

    # ======================================================
    # TABLEAU PAR GROUPE DE CHARGES
    # ======================================================
    st.subheader("📊 Dépenses par groupe de charges")

    df_group = (
        df_f
        .groupby("groupe_charges", as_index=False)
        .agg(
            montant_total=("montant_ttc", "sum"),
            nb_lignes=("depense_id", "count")
        )
        .sort_values("groupe_charges")
    )

    df_group["montant_total"] = df_group["montant_total"].apply(euro)

    st.dataframe(
        df_group.rename(columns={
            "groupe_charges": "Groupe de charges",
            "montant_total": "Montant total",
            "nb_lignes": "Nombre de lignes"
        }),
        use_container_width=True
    )

    # ======================================================
    # DÉTAIL DES DÉPENSES
    # ======================================================
    st.subheader("📋 Détail des dépenses")

    df_detail = (
        df_f[[
            "date",
            "compte",
            "poste",
            "fournisseur",
            "groupe_charges",
            "montant_ttc",
            "lot_id",
            "commentaire"
        ]]
        .sort_values("date")
    )

    df_detail["montant_ttc"] = df_detail["montant_ttc"].apply(euro)

    st.dataframe(
        df_detail.rename(columns={
            "date": "Date",
            "compte": "Compte",
            "poste": "Poste",
            "fournisseur": "Fournisseur",
            "groupe_charges": "Groupe de charges",
            "montant_ttc": "Montant TTC",
            "lot_id": "Lot",
            "commentaire": "Commentaire"
        }),
        use_container_width=True
    )