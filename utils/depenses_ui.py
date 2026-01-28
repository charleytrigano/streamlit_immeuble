import streamlit as st
import pandas as pd
from datetime import date

# =========================
# UTIL
# =========================
def euro(x):
    try:
        return f"{float(x):,.2f} €".replace(",", " ").replace(".", ",")
    except Exception:
        return "0,00 €"


# =========================
# UI DEPENSES
# =========================
def depenses_ui(supabase, annee):
    st.subheader("📄 État des dépenses")

    # =========================
    # CHARGEMENT DES DONNÉES
    # =========================
    dep_resp = (
        supabase
        .table("depenses")
        .select("*")
        .eq("annee", annee)
        .execute()
    )
    df = pd.DataFrame(dep_resp.data or [])

    bud_resp = (
        supabase
        .table("budgets")
        .select("annee, budget")
        .eq("annee", annee)
        .execute()
    )
    df_budget = pd.DataFrame(bud_resp.data or [])

    plan_resp = (
        supabase
        .table("plan_comptable")
        .select("*")
        .execute()
    )
    df_plan = pd.DataFrame(plan_resp.data or [])

    if df.empty:
        st.warning("Aucune dépense pour cette année.")
        return

    # =========================
    # ENRICHISSEMENT
    # =========================
    df["compte"] = df["compte"].astype(str)
    df["montant_ttc"] = pd.to_numeric(df["montant_ttc"], errors="coerce").fillna(0)

    # rattachement plan comptable
    if not df_plan.empty:
        df = df.merge(
            df_plan[["compte_8", "groupe_compte", "libelle", "libelle_groupe"]],
            left_on="compte",
            right_on="compte_8",
            how="left"
        )

    # =========================
    # FILTRES
    # =========================
    st.markdown("### 🔎 Filtres")

    colf1, colf2, colf3, colf4 = st.columns(4)

    with colf1:
        compte_f = st.selectbox(
            "Compte",
            ["Tous"] + sorted(df["compte"].dropna().unique().tolist())
        )

    with colf2:
        fournisseur_f = st.selectbox(
            "Fournisseur",
            ["Tous"] + sorted(df["fournisseur"].dropna().unique().tolist())
        )

    with colf3:
        poste_f = st.selectbox(
            "Poste",
            ["Tous"] + sorted(df["poste"].dropna().unique().tolist())
        )

    with colf4:
        groupe_f = st.selectbox(
            "Groupe de compte",
            ["Tous"] + sorted(df["groupe_compte"].dropna().unique().tolist())
        )

    df_f = df.copy()

    if compte_f != "Tous":
        df_f = df_f[df_f["compte"] == compte_f]

    if fournisseur_f != "Tous":
        df_f = df_f[df_f["fournisseur"] == fournisseur_f]

    if poste_f != "Tous":
        df_f = df_f[df_f["poste"] == poste_f]

    if groupe_f != "Tous":
        df_f = df_f[df_f["groupe_compte"] == groupe_f]

    # =========================
    # KPI
    # =========================
    total_dep = df_f["montant_ttc"].sum()
    budget_total = df_budget["budget"].sum() if not df_budget.empty else 0
    ecart = total_dep - budget_total
    ecart_pct = (ecart / budget_total * 100) if budget_total != 0 else 0

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Total dépenses", euro(total_dep))
    c2.metric("Budget", euro(budget_total))
    c3.metric("Écart", euro(ecart))
    c4.metric("Écart %", f"{ecart_pct:.2f} %")

    # =========================
    # TABLEAU
    # =========================
    st.markdown("### 📋 Détail des dépenses")

    st.dataframe(
        df_f[[
            "date",
            "compte",
            "libelle",
            "poste",
            "fournisseur",
            "montant_ttc",
            "type",
            "commentaire",
            "facture_url"
        ]].sort_values("date", ascending=False),
        use_container_width=True
    )

    # =========================
    # AJOUT
    # =========================
    st.markdown("### ➕ Ajouter une dépense")

    with st.form("add_depense"):
        d_date = st.date_input("Date", value=date.today())
        d_compte = st.text_input("Compte (8 chiffres)")
        d_poste = st.text_input("Poste")
        d_four = st.text_input("Fournisseur")
        d_montant = st.number_input("Montant TTC", step=0.01)
        d_type = st.selectbox("Type", ["Charge", "Avoir", "Remboursement"])
        d_comm = st.text_area("Commentaire")

        submitted = st.form_submit_button("Ajouter")

        if submitted:
            supabase.table("depenses").insert({
                "annee": annee,
                "date": d_date.isoformat(),
                "compte": d_compte,
                "poste": d_poste,
                "fournisseur": d_four,
                "montant_ttc": d_montant,
                "type": d_type,
                "commentaire": d_comm
            }).execute()

            st.success("Dépense ajoutée")
            st.rerun()

    # =========================
    # SUPPRESSION
    # =========================
    st.markdown("### 🗑️ Supprimer une dépense")

    if not df_f.empty:
        dep_map = {
            f"{row['date']} | {row['fournisseur']} | {euro(row['montant_ttc'])}":
            row["depense_id"]
            for _, row in df_f.iterrows()
        }

        sel = st.selectbox("Sélection", list(dep_map.keys()))
        if st.button("Supprimer"):
            supabase.table("depenses").delete().eq(
                "depense_id", dep_map[sel]
            ).execute()
            st.success("Dépense supprimée")
            st.rerun()