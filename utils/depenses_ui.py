import streamlit as st
import pandas as pd


# =========================
# OUTILS
# =========================
def euro(v):
    return f"{v:,.2f} €".replace(",", " ").replace(".", ",")


# =========================
# UI ÉTAT DES DÉPENSES
# =========================
def depenses_ui(supabase):

    st.title("📄 État des dépenses")

    # =========================
    # CHARGEMENT DONNÉES
    # =========================
    dep_resp = supabase.table("depenses").select("*").execute()
    plan_resp = supabase.table("plan_comptable").select("*").execute()
    bud_resp = supabase.table("budgets").select("*").execute()

    df_dep = pd.DataFrame(dep_resp.data)
    df_plan = pd.DataFrame(plan_resp.data)
    df_bud = pd.DataFrame(bud_resp.data)

    if df_dep.empty:
        st.warning("Aucune dépense enregistrée.")
        return

    # =========================
    # ENRICHISSEMENT PLAN COMPTABLE
    # =========================
    df = df_dep.merge(
        df_plan,
        left_on="compte",
        right_on="compte_8",
        how="left"
    )

    # =========================
    # SIDEBAR – FILTRES
    # =========================
    st.sidebar.header("🔎 Filtres")

    annee = st.sidebar.selectbox(
        "Année",
        sorted(df["annee"].dropna().unique().tolist())
    )

    df_f = df[df["annee"] == annee]

    groupe = st.sidebar.selectbox(
        "Groupe de compte",
        ["Tous"] + sorted(df_f["groupe_compte"].dropna().unique().tolist())
    )
    if groupe != "Tous":
        df_f = df_f[df_f["groupe_compte"] == groupe]

    compte = st.sidebar.selectbox(
        "Compte",
        ["Tous"] + sorted(df_f["compte"].dropna().unique().tolist())
    )
    if compte != "Tous":
        df_f = df_f[df_f["compte"] == compte]

    fournisseur = st.sidebar.selectbox(
        "Fournisseur",
        ["Tous"] + sorted(df_f["fournisseur"].dropna().unique().tolist())
    )
    if fournisseur != "Tous":
        df_f = df_f[df_f["fournisseur"] == fournisseur]

    poste = st.sidebar.selectbox(
        "Poste",
        ["Tous"] + sorted(df_f["poste"].dropna().unique().tolist())
    )
    if poste != "Tous":
        df_f = df_f[df_f["poste"] == poste]

    # =========================
    # KPI
    # =========================
    total_dep = df_f["montant_ttc"].sum()
    nb_dep = len(df_f)
    moy_dep = total_dep / nb_dep if nb_dep else 0

    # Budget associé (par groupe)
    df_bud_y = df_bud[df_bud["annee"] == annee]
    budget_total = (
        df_f[["groupe_compte"]]
        .dropna()
        .merge(df_bud_y, on="groupe_compte", how="left")["budget"]
        .sum()
    )

    ecart = total_dep - budget_total
    ecart_pct = (ecart / budget_total * 100) if budget_total else 0

    col1, col2, col3, col4, col5 = st.columns(5)
    col1.metric("Total dépenses", euro(total_dep))
    col2.metric("Nb dépenses", nb_dep)
    col3.metric("Dépense moyenne", euro(moy_dep))
    col4.metric("Budget", euro(budget_total))
    col5.metric("Écart", f"{euro(ecart)} ({ecart_pct:.1f} %)")

    # =========================
    # TABLEAU
    # =========================
    df_f["facture"] = df_f["facture_url"].fillna(df_f["pdf_url"])

    st.dataframe(
        df_f[[
            "date",
            "annee",
            "groupe_compte",
            "libelle_groupe",
            "compte",
            "poste",
            "fournisseur",
            "montant_ttc",
            "sens",
            "commentaire",
            "facture"
        ]].sort_values("date"),
        use_container_width=True
    )

    # =========================
    # AJOUT
    # =========================
    st.subheader("➕ Ajouter une dépense")

    with st.form("add_dep"):
        c1, c2, c3 = st.columns(3)
        date = c1.date_input("Date")
        annee_f = c2.number_input("Année", value=annee)
        compte_f = c3.text_input("Compte (8 chiffres)")

        poste_f = st.text_input("Poste")
        fournisseur_f = st.text_input("Fournisseur")
        montant_f = st.number_input("Montant TTC", step=0.01)
        sens_f = st.selectbox("Sens", ["Charge", "Avoir", "Remboursement"])
        commentaire_f = st.text_area("Commentaire")
        facture_url_f = st.text_input("Lien facture")

        if st.form_submit_button("Enregistrer"):
            supabase.table("depenses").insert({
                "date": str(date),
                "annee": annee_f,
                "compte": compte_f,
                "poste": poste_f,
                "fournisseur": fournisseur_f,
                "montant_ttc": montant_f,
                "sens": sens_f,
                "commentaire": commentaire_f,
                "facture_url": facture_url_f
            }).execute()
            st.experimental_rerun()

    # =========================
    # MODIFIER / SUPPRIMER
    # =========================
    st.subheader("✏️ Modifier / 🗑 Supprimer")

    dep_id = st.selectbox(
        "Sélectionner une dépense",
        df_f["depense_id"].tolist()
    )

    dep = df_dep[df_dep["depense_id"] == dep_id].iloc[0]

    if st.button("🗑 Supprimer"):
        supabase.table("depenses").delete().eq("depense_id", dep_id).execute()
        st.experimental_rerun()