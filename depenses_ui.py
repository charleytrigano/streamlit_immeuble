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
    resp = (
        supabase
        .table("depenses")
        .select("""
            depense_id,
            annee,
            compte,
            poste,
            fournisseur,
            date,
            montant_ttc,
            lot_id
        """)
        .eq("annee", annee)
        .execute()
    )

    if not resp.data:
        st.info("Aucune dépense pour cette année.")
        return

    df = pd.DataFrame(resp.data)

    # ======================================================
    # SÉCURISATION ABSOLUE DES COLONNES
    # ======================================================
    colonnes = [
        "depense_id",
        "annee",
        "compte",
        "poste",
        "fournisseur",
        "date",
        "montant_ttc",
        "lot_id",
    ]

    for col in colonnes:
        if col not in df.columns:
            df[col] = ""

    df["fournisseur"] = df["fournisseur"].fillna("")
    df["poste"] = df["poste"].fillna("")
    df["compte"] = df["compte"].fillna("")

    # ======================================================
    # PLAN COMPTABLE → GROUPE DE CHARGES
    # ======================================================
    plan = (
        supabase
        .table("plan_comptable")
        .select("compte_8, groupe_charges")
        .execute()
    )

    if plan.data:
        df_plan = pd.DataFrame(plan.data)

        df = df.merge(
            df_plan,
            left_on="compte",
            right_on="compte_8",
            how="left"
        )
    else:
        df["groupe_charges"] = "Non affecté"

    if "groupe_charges" not in df.columns:
        df["groupe_charges"] = "Non affecté"

    df["groupe_charges"] = df["groupe_charges"].fillna("Non affecté")

    # ======================================================
    # FILTRES
    # ======================================================
    st.subheader("🔎 Filtres")

    col1, col2, col3 = st.columns(3)

    with col1:
        fournisseurs = ["Tous"] + sorted(
            df["fournisseur"].astype(str).unique().tolist()
        )
        fournisseur_sel = st.selectbox(
            "Fournisseur",
            fournisseurs,
            key="filtre_fournisseur"
        )

    with col2:
        groupes = ["Tous"] + sorted(
            df["groupe_charges"].astype(str).unique().tolist()
        )
        groupe_sel = st.selectbox(
            "Groupe de charges",
            groupes,
            key="filtre_groupe"
        )

    with col3:
        comptes = ["Tous"] + sorted(
            df["compte"].astype(str).unique().tolist()
        )
        compte_sel = st.selectbox(
            "Compte",
            comptes,
            key="filtre_compte"
        )

    # ======================================================
    # APPLICATION DES FILTRES
    # ======================================================
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
    total = df_f["montant_ttc"].sum()
    nb = len(df_f)
    moy = total / nb if nb else 0

    c1, c2, c3 = st.columns(3)
    c1.metric("Total dépenses", euro(total))
    c2.metric("Nombre de lignes", nb)
    c3.metric("Dépense moyenne", euro(moy))

    # ======================================================
    # TABLEAU DÉTAILLÉ
    # ======================================================
    st.subheader("📋 Détail des dépenses")

    st.dataframe(
        df_f[[
            "date",
            "compte",
            "poste",
            "fournisseur",
            "groupe_charges",
            "montant_ttc",
            "lot_id"
        ]].sort_values("date"),
        use_container_width=True
    )

    # ======================================================
    # AGRÉGATION PAR GROUPE DE CHARGES
    # ======================================================
    st.subheader("📊 Dépenses par groupe de charges")

    grp = (
        df_f
        .groupby("groupe_charges", as_index=False)
        .agg(
            total=("montant_ttc", "sum"),
            lignes=("depense_id", "count")
        )
        .sort_values("total", ascending=False)
    )

    grp["Total"] = grp["total"].apply(euro)

    st.dataframe(
        grp[["groupe_charges", "Total", "lignes"]],
        use_container_width=True
    )