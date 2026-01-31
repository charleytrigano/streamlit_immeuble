import streamlit as st
import pandas as pd


def euro(x) -> str:
    """Format € sécurisé."""
    try:
        return f"{float(x):,.2f} €".replace(",", " ").replace(".", ",")
    except Exception:
        return "0,00 €"


def depenses_ui(supabase, annee: int):
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

    # Normalisation types
    df_dep["montant_ttc"] = pd.to_numeric(df_dep["montant_ttc"], errors="coerce").fillna(0)
    df_dep["date"] = pd.to_datetime(df_dep["date"], errors="coerce")

    # =========================
    # CHARGEMENT PLAN COMPTABLE
    # =========================
    resp_plan = (
        supabase
        .table("plan_comptable")
        .select("compte_8, libelle, groupe_compte, libelle_groupe, groupe_charges")
        .execute()
    )

    if resp_plan.data:
        df_plan = pd.DataFrame(resp_plan.data)
    else:
        # au cas où, pour éviter un crash
        df_plan = pd.DataFrame(
            columns=["compte_8", "libelle", "groupe_compte", "libelle_groupe", "groupe_charges"]
        )

    # =========================
    # JOINTURE DÉPENSES ↔ PLAN COMPTABLE
    # =========================
    # On suppose : depenses.compte contient le même codage que plan_comptable.compte_8
    df = df_dep.merge(
        df_plan,
        left_on="compte",
        right_on="compte_8",
        how="left"
    )

    # Sécurisation colonne groupe_charges (au cas où il y a des NULL)
    if "groupe_charges" not in df.columns:
        df["groupe_charges"] = None

    # =========================
    # FILTRES
    # =========================
    st.subheader("🔎 Filtres")

    col1, col2, col3 = st.columns(3)

    # Groupe de charges
    with col1:
        groupes = (
            ["Tous"]
            + sorted(
                [g for g in df["groupe_charges"].dropna().unique().tolist() if g != ""]
            )
        )
        groupe_sel = st.selectbox("Groupe de charges", groupes, index=0)

    # Fournisseur
    with col2:
        fournisseurs = (
            ["Tous"]
            + sorted(
                [f for f in df["fournisseur"].dropna().unique().tolist() if f != ""]
            )
        )
        fournisseur_sel = st.selectbox("Fournisseur", fournisseurs, index=0)

    # Compte comptable
    with col3:
        comptes = (
            ["Tous"]
            + sorted(
                [c for c in df["compte"].dropna().unique().tolist() if c != ""]
            )
        )
        compte_sel = st.selectbox("Compte", comptes, index=0)

    # Application des filtres
    df_f = df.copy()

    if groupe_sel != "Tous":
        df_f = df_f[df_f["groupe_charges"] == groupe_sel]

    if fournisseur_sel != "Tous":
        df_f = df_f[df_f["fournisseur"] == fournisseur_sel]

    if compte_sel != "Tous":
        df_f = df_f[df_f["compte"] == compte_sel]

    if df_f.empty:
        st.warning("Aucune dépense après application des filtres.")
        return

    # =========================
    # KPI GLOBAUX
    # =========================
    total = df_f["montant_ttc"].sum()
    nb = len(df_f)
    moy = total / nb if nb else 0

    k1, k2, k3 = st.columns(3)
    k1.metric("Total dépenses", euro(total))
    k2.metric("Nombre d'écritures", nb)
    k3.metric("Dépense moyenne", euro(moy))

    # =========================
    # TABLEAU PAR GROUPE DE CHARGES
    # =========================
    st.subheader("📊 Dépenses par groupe de charges")

    df_group = (
        df_f
        .groupby(["groupe_charges"], dropna=False, as_index=False)
        .agg(
            montant_total=("montant_ttc", "sum"),
            nb_lignes=("depense_id", "count")
        )
        .sort_values("groupe_charges", na_position="last")
    )

    df_group["montant_total_fmt"] = df_group["montant_total"].apply(euro)

    st.dataframe(
        df_group[["groupe_charges", "montant_total_fmt", "nb_lignes"]]
        .rename(columns={
            "groupe_charges": "Groupe de charges",
            "montant_total_fmt": "Montant total",
            "nb_lignes": "Nombre de lignes"
        }),
        use_container_width=True,
    )

    # =========================
    # TABLEAU DÉTAIL
    # =========================
    st.subheader("📋 Détail des écritures filtrées")

    df_detail = df_f.copy()
    df_detail["date"] = df_detail["date"].dt.date

    st.dataframe(
        df_detail[[
            "date",
            "compte",
            "poste",
            "fournisseur",
            "groupe_charges",
            "montant_ttc",
        ]].sort_values("date"),
        use_container_width=True,
    )