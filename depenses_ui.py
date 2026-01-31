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
    # CHARGEMENT DEPENSES
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
    # CHARGEMENT PLAN COMPTABLE
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
    # NORMALISATION STRICTE (AUCUN TRI)
    # ======================================================
    df["groupe_charges"] = df["groupe_charges"].fillna("Non affecté").astype(str)

    # ======================================================
    # FILTRES
    # ======================================================
    st.subheader("🔎 Filtres")

    col1, col2, col3 = st.columns(3)

    with col1:
        groupes = ["Tous"] + list(df["groupe_charges"].unique())
        groupe_sel = st.selectbox("Groupe de charges", groupes)

    with col2:
        fournisseurs = ["Tous"] + list(df["fournisseur"].dropna().astype(str).unique())
        fournisseur_sel = st.selectbox("Fournisseur", fournisseurs)

    with col3:
        postes = ["Tous"] + list(df["poste"].dropna().astype(str).unique())
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
    # TABLEAU PAR GROUPE DE CHARGES (SANS TRI)
    # ======================================================
    st.subheader("📊 Dépenses par groupe de charges")

    df_group = (
        df_f
        .groupby("groupe_charges", dropna=False, as_index=False)
        .agg(
            montant_total=("montant_ttc", "sum"),
            nb_lignes=("depense_id", "count")
        )
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
    # DETAIL DES DEPENSES (SANS TRI)
    # ======================================================
    st.subheader("📋 Détail des dépenses")

    df_detail = df_f[[
        "date",
        "compte",
        "poste",
        "fournisseur",
        "groupe_charges",
        "montant_ttc",
        "lot_id",
        "commentaire"
    ]].copy()

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