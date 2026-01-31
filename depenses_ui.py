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
    # DÉPENSES
    # ======================================================
    dep_resp = (
        supabase
        .table("depenses")
        .select(
            "depense_id, annee, compte, poste, fournisseur, date, montant_ttc, lot_id"
        )
        .eq("annee", annee)
        .execute()
    )

    if not dep_resp.data:
        st.info("Aucune dépense pour cette année.")
        return

    df_dep = pd.DataFrame(dep_resp.data)

    # ======================================================
    # PLAN COMPTABLE
    # ======================================================
    plan_resp = (
        supabase
        .table("plan_comptable")
        .select("compte_8, libelle, groupe_charges")
        .execute()
    )

    df_plan = pd.DataFrame(plan_resp.data)

    # ======================================================
    # JOINTURE
    # ======================================================
    if not df_plan.empty:
        df = df_dep.merge(
            df_plan,
            left_on="compte",
            right_on="compte_8",
            how="left"
        )
    else:
        df = df_dep.copy()

    # ======================================================
    # 🔐 SÉCURISATION ABSOLUE DES COLONNES
    # ======================================================
    if "groupe_charges" not in df.columns:
        df["groupe_charges"] = "Non affecté"

    if "libelle" not in df.columns:
        df["libelle"] = ""

    df["groupe_charges"] = df["groupe_charges"].fillna("Non affecté")

    # ======================================================
    # FILTRES
    # ======================================================
    st.subheader("🔎 Filtres")

    colf1, colf2, colf3 = st.columns(3)

    with colf1:
        fournisseurs = ["Tous"] + sorted(df["fournisseur"].dropna().unique().tolist())
        fournisseur_sel = st.selectbox("Fournisseur", fournisseurs)

    with colf2:
        groupes = ["Tous"] + sorted(df["groupe_charges"].astype(str).unique().tolist())
        groupe_sel = st.selectbox("Groupe de charges", groupes)

    with colf3:
        comptes = ["Tous"] + sorted(df["compte"].dropna().unique().tolist())
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
    total = df_f["montant_ttc"].sum()
    nb = len(df_f)
    moy = total / nb if nb else 0

    c1, c2, c3 = st.columns(3)
    c1.metric("Total dépenses", euro(total))
    c2.metric("Nombre de lignes", nb)
    c3.metric("Dépense moyenne", euro(moy))

    # ======================================================
    # TABLEAU
    # ======================================================
    st.subheader("📋 Détail des dépenses")

    st.dataframe(
        df_f[[
            "date",
            "compte",
            "libelle",
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