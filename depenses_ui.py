import streamlit as st
import pandas as pd
from datetime import date


def euro(x):
    try:
        return f"{float(x):,.2f} €".replace(",", " ").replace(".", ",")
    except Exception:
        return "0,00 €"


def depenses_ui(supabase, annee):
    st.header(f"📄 Dépenses – {annee}")

    # ======================================================
    # LECTURE VIA LA VUE ENRICHIE
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
        df = pd.DataFrame()
    else:
        df = pd.DataFrame(resp.data)

    # Sécurisation minimale
    if df.empty:
        return

    df["montant_ttc"] = pd.to_numeric(df["montant_ttc"], errors="coerce").fillna(0)

    has_fournisseur = "fournisseur" in df.columns

    # ======================================================
    # FILTRES
    # ======================================================
    st.subheader("🔎 Filtres")

    c1, c2, c3, c4 = st.columns(4)

    with c1:
        groupes = ["Tous"] + sorted(df["groupe_charges"].dropna().unique().tolist())
        groupe_sel = st.selectbox("Groupe de charges", groupes)

    with c2:
        comptes = ["Tous"] + sorted(df["compte"].dropna().unique().tolist())
        compte_sel = st.selectbox("Compte", comptes)

    with c3:
        postes = ["Tous"] + sorted(df["poste"].dropna().unique().tolist())
        poste_sel = st.selectbox("Poste", postes)

    with c4:
        if has_fournisseur:
            fournisseurs = ["Tous"] + sorted(df["fournisseur"].dropna().unique().tolist())
            fournisseur_sel = st.selectbox("Fournisseur", fournisseurs)
        else:
            fournisseur_sel = "Tous"
            st.caption("Fournisseur non disponible")

    # ======================================================
    # APPLICATION DES FILTRES
    # ======================================================
    df_f = df.copy()

    if groupe_sel != "Tous":
        df_f = df_f[df_f["groupe_charges"] == groupe_sel]

    if compte_sel != "Tous":
        df_f = df_f[df_f["compte"] == compte_sel]

    if poste_sel != "Tous":
        df_f = df_f[df_f["poste"] == poste_sel]

    if has_fournisseur and fournisseur_sel != "Tous":
        df_f = df_f[df_f["fournisseur"] == fournisseur_sel]

    # ======================================================
    # KPI
    # ======================================================
    st.subheader("📊 Indicateurs")

    total_dep = df_f["montant_ttc"].sum()
    nb = len(df_f)
    moy = total_dep / nb if nb else 0

    k1, k2, k3 = st.columns(3)
    k1.metric("💸 Total dépenses", euro(total_dep))
    k2.metric("🧾 Lignes", nb)
    k3.metric("📊 Moyenne", euro(moy))

    # ======================================================
    # DÉPENSES PAR GROUPE
    # ======================================================
    st.subheader("📊 Dépenses par groupe de charges")

    df_group = (
        df_f
        .groupby("groupe_charges", as_index=False)
        .agg(total=("montant_ttc", "sum"))
        .sort_values("groupe_charges")
    )

    df_group["total"] = df_group["total"].apply(euro)
    st.dataframe(df_group, use_container_width=True)

    # ======================================================
    # DÉTAIL DES DÉPENSES
    # ======================================================
    st.subheader("📋 Détail des dépenses")

    df_detail = df_f[[
        "depense_id",
        "date",
        "compte",
        "libelle_compte",
        "poste",
        "montant_ttc",
        "groupe_charges"
    ]].copy()

    df_detail["montant_ttc"] = df_detail["montant_ttc"].apply(euro)
    st.dataframe(df_detail, use_container_width=True)

    # ======================================================
    # AJOUT DÉPENSE
    # ======================================================
    st.divider()
    st.subheader("➕ Ajouter une dépense")

    with st.form("add_depense"):
        d_date = st.date_input("Date", value=date.today())
        d_compte = st.text_input("Compte (8 chiffres)")
        d_poste = st.text_input("Poste")
        d_montant = st.number_input("Montant TTC", min_value=0.0, step=10.0)
        d_fournisseur = st.text_input("Fournisseur")
        ok = st.form_submit_button("Ajouter")

        if ok:
            supabase.table("depenses").insert({
                "annee": annee,
                "date": d_date.isoformat(),
                "compte": d_compte,
                "poste": d_poste,
                "montant_ttc": d_montant,
                "fournisseur": d_fournisseur
            }).execute()
            st.success("Dépense ajoutée")
            st.rerun()

    # ======================================================
    # MODIFIER / SUPPRIMER
    # ======================================================
    st.subheader("✏️ Modifier / Supprimer une dépense")

    dep_id = st.selectbox(
        "Sélectionner une dépense",
        df_f["depense_id"].tolist()
    )

    dep = df_f[df_f["depense_id"] == dep_id].iloc[0]

    m_poste = st.text_input("Poste", dep["poste"])
    m_montant = st.number_input(
        "Montant TTC",
        value=float(dep["montant_ttc"]),
        step=10.0
    )

    cA, cB = st.columns(2)

    with cA:
        if st.button("💾 Enregistrer"):
            supabase.table("depenses").update({
                "poste": m_poste,
                "montant_ttc": m_montant
            }).eq("id", dep_id).execute()
            st.success("Dépense modifiée")
            st.rerun()

    with cB:
        if st.button("🗑️ Supprimer"):
            supabase.table("depenses").delete().eq("id", dep_id).execute()
            st.warning("Dépense supprimée")
            st.rerun()