import streamlit as st
import pandas as pd


def euro(x):
    return f"{x:,.2f} €".replace(",", " ").replace(".", ",")


def depenses_ui(supabase, annee):
    st.header(f"📄 Dépenses – {annee}")

    # =========================
    # CHARGEMENT DÉPENSES
    # =========================
    dep_resp = (
        supabase
        .table("depenses")
        .select("""
            depense_id,
            annee,
            compte,
            poste,
            fournisseur,
            date,
            montant_ttc
        """)
        .eq("annee", annee)
        .execute()
    )

    if not dep_resp.data:
        st.info("Aucune dépense pour cette année.")
        return

    df = pd.DataFrame(dep_resp.data)

    # =========================
    # PLAN COMPTABLE (groupes)
    # =========================
    plan_resp = (
        supabase
        .table("plan_comptable")
        .select("""
            compte_8,
            groupe_charges,
            libelle
        """)
        .execute()
    )

    df_plan = pd.DataFrame(plan_resp.data)

    df = df.merge(
        df_plan,
        left_on="compte",
        right_on="compte_8",
        how="left"
    )

    # =========================
    # LIBELLÉS DES GROUPES
    # =========================
    groupes = {
        1: "Charges communes générales",
        2: "Charges spéciales RDC / sous-sols",
        3: "Charges spéciales sous-sols",
        4: "Ascenseurs",
        5: "Charges garages / parkings",
        6: "Monte-voitures",
    }

    df["groupe_charges_label"] = df["groupe_charges"].map(groupes)

    # =========================
    # FILTRES
    # =========================
    st.markdown("### 🔎 Filtres")

    col1, col2, col3 = st.columns(3)

    f_groupes = sorted(df["groupe_charges_label"].dropna().unique())
    f_comptes = sorted(df["compte"].dropna().unique())
    f_fournisseurs = sorted(df["fournisseur"].dropna().unique())

    sel_groupes = col1.multiselect(
        "Groupe de charges",
        ["Tous"] + f_groupes,
        default=["Tous"]
    )

    sel_comptes = col2.multiselect(
        "Compte",
        ["Tous"] + f_comptes,
        default=["Tous"]
    )

    sel_fournisseurs = col3.multiselect(
        "Fournisseur",
        ["Tous"] + f_fournisseurs,
        default=["Tous"]
    )

    df_f = df.copy()

    if "Tous" not in sel_groupes:
        df_f = df_f[df_f["groupe_charges_label"].isin(sel_groupes)]

    if "Tous" not in sel_comptes:
        df_f = df_f[df_f["compte"].isin(sel_comptes)]

    if "Tous" not in sel_fournisseurs:
        df_f = df_f[df_f["fournisseur"].isin(sel_fournisseurs)]

    # =========================
    # KPI
    # =========================
    total = df_f["montant_ttc"].sum()
    nb = len(df_f)
    moy = total / nb if nb else 0

    c1, c2, c3 = st.columns(3)
    c1.metric("Total dépenses", euro(total))
    c2.metric("Nombre de lignes", nb)
    c3.metric("Dépense moyenne", euro(moy))

    # =========================
    # TABLEAU DÉTAIL
    # =========================
    st.markdown("### 📋 Détail des dépenses")

    st.dataframe(
        df_f[[
            "date",
            "compte",
            "poste",
            "fournisseur",
            "groupe_charges_label",
            "montant_ttc"
        ]].rename(columns={
            "date": "Date",
            "compte": "Compte",
            "poste": "Poste",
            "fournisseur": "Fournisseur",
            "groupe_charges_label": "Groupe de charges",
            "montant_ttc": "Montant TTC (€)"
        }).sort_values("date"),
        use_container_width=True
    )

    # =========================
    # SYNTHÈSE PAR GROUPE
    # =========================
    st.markdown("### 📊 Dépenses par groupe de charges")

    synthese = (
        df_f
        .groupby("groupe_charges_label", as_index=False)
        .agg(
            total=("montant_ttc", "sum"),
            nb=("depense_id", "count")
        )
        .sort_values("total", ascending=False)
    )

    st.dataframe(
        synthese.rename(columns={
            "groupe_charges_label": "Groupe de charges",
            "total": "Total (€)",
            "nb": "Nombre de dépenses"
        }),
        use_container_width=True
    )