import streamlit as st
import pandas as pd


def euro(x):
    try:
        return f"{float(x):,.2f} €".replace(",", " ").replace(".", ",")
    except Exception:
        return "0,00 €"


def depenses_ui(supabase, annee):
    st.header(f"📄 Dépenses – {annee}")

    # =========================
    # CHARGEMENT DÉPENSES
    # =========================
    resp_dep = (
        supabase
        .table("depenses")
        .select("depense_id, annee, compte, poste, fournisseur, date, montant_ttc")
        .eq("annee", annee)
        .execute()
    )

    if not resp_dep.data:
        st.info("Aucune dépense pour cette année.")
        return

    df_dep = pd.DataFrame(resp_dep.data)

    df_dep["montant_ttc"] = pd.to_numeric(df_dep["montant_ttc"], errors="coerce").fillna(0)
    df_dep["date"] = pd.to_datetime(df_dep["date"], errors="coerce")

    # =========================
    # CHARGEMENT PLAN COMPTABLE
    # =========================
    resp_plan = (
        supabase
        .table("plan_comptable")
        .select("compte_8, groupe_charges")
        .execute()
    )

    if resp_plan.data:
        df_plan = pd.DataFrame(resp_plan.data)
    else:
        df_plan = pd.DataFrame(columns=["compte_8", "groupe_charges"])

    # =========================
    # JOINTURE
    # =========================
    df = df_dep.merge(
        df_plan,
        left_on="compte",
        right_on="compte_8",
        how="left"
    )

    if "groupe_charges" not in df.columns:
        df["groupe_charges"] = "Non affecté"

    df["groupe_charges"] = df["groupe_charges"].fillna("Non affecté")

    # =========================
    # FILTRES
    # =========================
    st.subheader("🔎 Filtres")

    col1, col2, col3 = st.columns(3)

    with col1:
        groupes = ["Tous"] + sorted(df["groupe_charges"].unique().tolist())
        groupe_sel = st.selectbox("Groupe de charges", groupes)

    with col2:
        fournisseurs = ["Tous"] + sorted(df["fournisseur"].dropna().unique().tolist())
        fournisseur_sel = st.selectbox("Fournisseur", fournisseurs)

    with col3:
        comptes = ["Tous"] + sorted(df["compte"].dropna().unique().tolist())
        compte_sel = st.selectbox("Compte", comptes)

    df_f = df.copy()

    if groupe_sel != "Tous":
        df_f = df_f[df_f["groupe_charges"] == groupe_sel]

    if fournisseur_sel != "Tous":
        df_f = df_f[df_f["fournisseur"] == fournisseur_sel]

    if compte_sel != "Tous":
        df_f = df_f[df_f["compte"] == compte_sel]

    if df_f.empty:
        st.warning("Aucune dépense après filtres.")
        return

    # =========================
    # KPI
    # =========================
    total = df_f["montant_ttc"].sum()
    nb = len(df_f)
    moyenne = total / nb if nb else 0

    k1, k2, k3 = st.columns(3)
    k1.metric("Total dépenses", euro(total))
    k2.metric("Nombre d’écritures", nb)
    k3.metric("Dépense moyenne", euro(moyenne))

    # =========================
    # TABLEAU PAR GROUPE DE CHARGES
    # =========================
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

    # =========================
    # DÉTAIL DES ÉCRITURES
    # =========================
    st.subheader("📋 Détail des dépenses")

    df_detail = df_f.copy()
    df_detail["date"] = df_detail["date"].dt.date

    st.dataframe(
        df_detail[[
            "date",
            "compte",
            "poste",
            "fournisseur",
            "groupe_charges",
            "montant_ttc"
        ]].sort_values("date"),
        use_container_width=True
    )