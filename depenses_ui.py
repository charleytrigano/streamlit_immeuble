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
    # CHARGEMENT DES DONNÉES
    # ======================================================
    dep_resp = (
        supabase
        .table("depenses")
        .select(
            "depense_id, annee, compte, poste, fournisseur, date, "
            "montant_ttc, lot_id"
        )
        .eq("annee", annee)
        .execute()
    )

    if not dep_resp.data:
        st.info("Aucune dépense pour cette année.")
        return

    df_dep = pd.DataFrame(dep_resp.data)

    plan_resp = (
        supabase
        .table("plan_comptable")
        .select("compte_8, libelle, groupe_charges")
        .execute()
    )

    df_plan = pd.DataFrame(plan_resp.data)

    # ======================================================
    # NORMALISATION / JOINTURE
    # ======================================================
    df = df_dep.merge(
        df_plan,
        left_on="compte",
        right_on="compte_8",
        how="left"
    )

    df["groupe_charges"] = df["groupe_charges"].fillna("Non affecté")

    # ======================================================
    # FILTRES
    # ======================================================
    st.subheader("🔎 Filtres")

    colf1, colf2, colf3 = st.columns(3)

    with colf1:
        fournisseurs = ["Tous"] + sorted(df["fournisseur"].dropna().unique())
        fournisseur_sel = st.selectbox("Fournisseur", fournisseurs)

    with colf2:
        groupes = ["Tous"] + sorted(df["groupe_charges"].dropna().unique())
        groupe_sel = st.selectbox("Groupe de charges", groupes)

    with colf3:
        comptes = ["Tous"] + sorted(df["compte"].dropna().unique())
        compte_sel = st.selectbox("Compte comptable", comptes)

    df_f = df.copy()

    if fournisseur_sel != "Tous":
        df_f = df_f[df_f["fournisseur"] == fournisseur_sel]

    if groupe_sel != "Tous":
        df_f = df_f[df_f["groupe_charges"] == groupe_sel]

    if compte_sel != "Tous":
        df_f = df_f[df_f["compte"] == compte_sel]

    # ======================================================
    # KPI
    # ======================================================
    total_dep = df_f["montant_ttc"].sum()
    nb_lignes = len(df_f)
    dep_moy = total_dep / nb_lignes if nb_lignes else 0

    col1, col2, col3 = st.columns(3)
    col1.metric("Total dépenses", euro(total_dep))
    col2.metric("Nombre de lignes", nb_lignes)
    col3.metric("Dépense moyenne", euro(dep_moy))

    # ======================================================
    # TABLEAU DÉTAILLÉ DES DÉPENSES
    # ======================================================
    st.subheader("📋 Détail des dépenses")

    df_aff = df_f[[
        "date",
        "compte",
        "libelle",
        "poste",
        "fournisseur",
        "groupe_charges",
        "montant_ttc",
        "lot_id"
    ]].rename(columns={
        "date": "Date",
        "compte": "Compte",
        "libelle": "Libellé compte",
        "poste": "Poste",
        "fournisseur": "Fournisseur",
        "groupe_charges": "Groupe de charges",
        "montant_ttc": "Montant TTC",
        "lot_id": "Lot"
    })

    df_aff = df_aff.sort_values("Date")

    st.dataframe(df_aff, use_container_width=True)

    # ======================================================
    # TABLEAU PAR GROUPE DE CHARGES
    # ======================================================
    st.subheader("📊 Dépenses par groupe de charges")

    df_grp = (
        df_f
        .groupby("groupe_charges", as_index=False)
        .agg(
            total=("montant_ttc", "sum"),
            nb_lignes=("depense_id", "count")
        )
        .sort_values("total", ascending=False)
    )

    df_grp["Total"] = df_grp["total"].apply(euro)

    st.dataframe(
        df_grp[["groupe_charges", "Total", "nb_lignes"]],
        use_container_width=True
    )