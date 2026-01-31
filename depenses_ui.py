import streamlit as st
import pandas as pd


def euro(x) -> str:
    """Formatage simple en euros."""
    try:
        return f"{float(x):,.2f} €".replace(",", " ").replace(".", ",")
    except Exception:
        return "0,00 €"


def depenses_ui(supabase, annee: int) -> None:
    st.header(f"📄 Dépenses – {annee}")

    # ======================================================
    # 1. CHARGEMENT DES DÉPENSES
    # ======================================================
    resp = (
        supabase
        .table("depenses")
        .select(
            """
            depense_id,
            annee,
            compte,
            poste,
            fournisseur,
            date,
            montant_ttc,
            lot_id
            """
        )
        .eq("annee", annee)
        .execute()
    )

    if not resp.data:
        st.info("Aucune dépense pour cette année.")
        return

    df = pd.DataFrame(resp.data)

    # Sécurisation des colonnes attendues
    expected_cols = [
        "depense_id",
        "annee",
        "compte",
        "poste",
        "fournisseur",
        "date",
        "montant_ttc",
        "lot_id",
    ]
    for col in expected_cols:
        if col not in df.columns:
            df[col] = None

    df["montant_ttc"] = pd.to_numeric(df["montant_ttc"], errors="coerce").fillna(0.0)
    df["date"] = pd.to_datetime(df["date"], errors="coerce")

    # ======================================================
    # 2. CHARGEMENT PLAN COMPTABLE → GROUPE DE CHARGES
    # ======================================================
    plan_resp = (
        supabase
        .table("plan_comptable")
        .select("compte_8, groupe_charges")
        .execute()
    )

    df["groupe_charges"] = "Non affecté"

    if plan_resp.data:
        df_plan = pd.DataFrame(plan_resp.data)

        # On vérifie que la colonne existe bien
        if "compte_8" in df_plan.columns:
            # jointure compte (dépenses) → compte_8 (plan comptable)
            df = df.merge(
                df_plan,
                left_on="compte",
                right_on="compte_8",
                how="left",
            )
            # Si pas de groupe_charges trouvé, on met "Non affecté"
            df["groupe_charges"] = df["groupe_charges"].fillna("Non affecté")
        else:
            # si la colonne n'existe pas, on ne casse pas l'app
            st.warning("⚠️ `compte_8` manquant dans `plan_comptable`. Pas de groupe de charges.")
    else:
        st.warning("⚠️ Aucun enregistrement dans `plan_comptable`. Pas de groupe de charges.")

    # ======================================================
    # 3. FILTRES (dans le cadre Dépenses uniquement)
    # ======================================================
    st.subheader("🔎 Filtres dépenses")

    col1, col2, col3 = st.columns(3)

    with col1:
        fournisseurs = ["Tous"] + sorted(
            [f for f in df["fournisseur"].dropna().unique().tolist() if f != ""]
        )
        fournisseur_sel = st.selectbox("Fournisseur", fournisseurs)

    with col2:
        groupes = ["Tous"] + sorted(
            [g for g in df["groupe_charges"].dropna().unique().tolist() if g != ""]
        )
        groupe_sel = st.selectbox("Groupe de charges", groupes)

    with col3:
        comptes = ["Tous"] + sorted(
            [c for c in df["compte"].dropna().unique().tolist() if c != ""]
        )
        compte_sel = st.selectbox("Compte", comptes)

    df_f = df.copy()

    if fournisseur_sel != "Tous":
        df_f = df_f[df_f["fournisseur"] == fournisseur_sel]

    if groupe_sel != "Tous":
        df_f = df_f[df_f["groupe_charges"] == groupe_sel]

    if compte_sel != "Tous":
        df_f = df_f[df_f["compte"] == compte_sel]

    # Si après filtres il n'y a plus de lignes
    if df_f.empty:
        st.warning("Aucune dépense ne correspond aux filtres.")
        return

    # ======================================================
    # 4. KPI
    # ======================================================
    total = df_f["montant_ttc"].sum()
    nb = len(df_f)
    moy = total / nb if nb else 0

    k1, k2, k3 = st.columns(3)
    k1.metric("Total dépenses", euro(total))
    k2.metric("Nombre de lignes", nb)
    k3.metric("Dépense moyenne", euro(moy))

    # ======================================================
    # 5. TABLEAU DÉTAILLÉ
    # ======================================================
    st.subheader("📋 Détail des dépenses")

    df_detail = df_f.copy()
    # Pour l'affichage, on re-formate la date
    df_detail["date"] = df_detail["date"].dt.date

    st.dataframe(
        df_detail[
            [
                "date",
                "compte",
                "poste",
                "fournisseur",
                "groupe_charges",
                "montant_ttc",
                "lot_id",
            ]
        ].sort_values("date"),
        use_container_width=True,
    )

    # ======================================================
    # 6. TABLEAU PAR GROUPE DE CHARGES
    # ======================================================
    st.subheader("📊 Dépenses par groupe de charges")

    grp = (
        df_f.groupby("groupe_charges", as_index=False)
        .agg(
            total=("montant_ttc", "sum"),
            lignes=("depense_id", "count"),
        )
        .sort_values("total", ascending=False)
    )

    grp["Total"] = grp["total"].apply(euro)

    st.dataframe(
        grp[["groupe_charges", "Total", "lignes"]],
        use_container_width=True,
    )