import streamlit as st
import pandas as pd


def euro(x):
    return f"{x:,.2f} €".replace(",", " ").replace(".", ",")


def depenses_ui(supabase, annee):
    st.header(f"📄 Dépenses – {annee}")

    # ======================================================
    # CHARGEMENT DES DONNÉES (VUE UNIQUE)
    # ======================================================
    resp = (
        supabase
        .table("v_depenses_enrichies")
        .select("*")
        .eq("annee", annee)
        .execute()
    )

    if not resp.data:
        st.info("Aucune dépense pour cette année.")
        return

    df = pd.DataFrame(resp.data)

    df["montant_ttc"] = pd.to_numeric(df["montant_ttc"], errors="coerce").fillna(0)

    # ======================================================
    # FILTRES
    # ======================================================
    st.subheader("🔎 Filtres")

    col1, col2, col3 = st.columns(3)

    with col1:
        groupes = ["Tous"] + sorted(df["groupe_charges"].dropna().unique().tolist())
        groupe_sel = st.selectbox("Groupe de charges", groupes)

    with col2:
        comptes = (
            ["Tous"]
            + sorted(
                df[["compte", "libelle_compte"]]
                .dropna()
                .drop_duplicates()
                .apply(
                    lambda x: f"{x['compte']} – {x['libelle_compte']}",
                    axis=1
                )
                .tolist()
            )
        )
        compte_sel = st.selectbox("Compte", comptes)

    with col3:
        postes = ["Tous"] + sorted(df["poste"].dropna().unique().tolist())
        poste_sel = st.selectbox("Poste", postes)

    # ======================================================
    # APPLICATION DES FILTRES
    # ======================================================
    df_f = df.copy()

    if groupe_sel != "Tous":
        df_f = df_f[df_f["groupe_charges"] == groupe_sel]

    if compte_sel != "Tous":
        code = compte_sel.split(" – ")[0]
        df_f = df_f[df_f["compte"] == code]

    if poste_sel != "Tous":
        df_f = df_f[df_f["poste"] == poste_sel]

    # ======================================================
    # KPI
    # ======================================================
    total_dep = df_f["montant_ttc"].sum()
    nb_lignes = len(df_f)
    dep_moy = total_dep / nb_lignes if nb_lignes else 0

    k1, k2, k3 = st.columns(3)
    k1.metric("💸 Total dépenses", euro(total_dep))
    k2.metric("🧾 Nombre de lignes", nb_lignes)
    k3.metric("📊 Dépense moyenne", euro(dep_moy))

    # ======================================================
    # DÉPENSES PAR GROUPE DE CHARGES
    # ======================================================
    st.subheader("📊 Dépenses par groupe de charges")

    df_group = (
        df_f
        .groupby("groupe_charges", as_index=False)
        .agg(
            total=("montant_ttc", "sum"),
            nb=("depense_id", "count")
        )
        .sort_values("groupe_charges")
    )

    df_group["total"] = df_group["total"].apply(euro)

    st.dataframe(
        df_group.rename(columns={
            "groupe_charges": "Groupe de charges",
            "total": "Total (€)",
            "nb": "Nb lignes"
        }),
        use_container_width=True
    )

    # ======================================================
    # DÉTAIL DES DÉPENSES
    # ======================================================
    st.subheader("📋 Détail des dépenses")

    df_detail = df_f[[
        "date",
        "compte",
        "libelle_compte",
        "poste",
        "montant_ttc",
        "groupe_charges"
    ]].copy()

    df_detail["montant_ttc"] = df_detail["montant_ttc"].apply(euro)

    st.dataframe(
        df_detail.rename(columns={
            "date": "Date",
            "compte": "Compte",
            "libelle_compte": "Libellé compte",
            "poste": "Poste",
            "montant_ttc": "Montant TTC",
            "groupe_charges": "Groupe de charges"
        }),
        use_container_width=True
    )