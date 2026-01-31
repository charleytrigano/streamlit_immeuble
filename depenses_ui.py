import streamlit as st
import pandas as pd
from datetime import date


def euro(x):
    try:
        return f"{x:,.2f} €".replace(",", " ").replace(".", ",")
    except Exception:
        return "0,00 €"


def depenses_ui(supabase, annee):
    st.header(f"📄 Dépenses – {annee}")

    # ======================================================
    # CHARGEMENT DES DÉPENSES (vue enrichie)
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
        comptes = ["Tous"] + sorted(df["compte"].dropna().unique().tolist())
        compte_sel = st.selectbox("Compte comptable", comptes)

    with col3:
        if "fournisseur" in df.columns:
            fournisseurs = ["Tous"] + sorted(df["fournisseur"].dropna().unique().tolist())
            fournisseur_sel = st.selectbox("Fournisseur", fournisseurs)
        else:
            fournisseur_sel = "Tous"

    df_f = df.copy()

    if groupe_sel != "Tous":
        df_f = df_f[df_f["groupe_charges"] == groupe_sel]

    if compte_sel != "Tous":
        df_f = df_f[df_f["compte"] == compte_sel]

    if fournisseur_sel != "Tous" and "fournisseur" in df_f.columns:
        df_f = df_f[df_f["fournisseur"] == fournisseur_sel]

    # ======================================================
    # TABLEAU 1 – BUDGET vs DÉPENSES PAR GROUPE
    # ======================================================
    st.subheader("💰 Budget vs Dépenses par groupe de charges")

    # Dépenses agrégées
    df_dep_group = (
        df_f
        .groupby("groupe_charges", as_index=False)
        .agg(depenses=("montant_ttc", "sum"))
    )

    # Budget
    bud_resp = (
        supabase
        .table("budget")
        .select("annee, groupe_charges, budget")
        .eq("annee", annee)
        .execute()
    )

    if bud_resp.data:
        df_budget = pd.DataFrame(bud_resp.data)
        df_budget["budget"] = pd.to_numeric(df_budget["budget"], errors="coerce").fillna(0)
    else:
        df_budget = pd.DataFrame(columns=["groupe_charges", "budget"])

    df_bvr = df_dep_group.merge(
        df_budget,
        on="groupe_charges",
        how="left"
    )

    df_bvr["budget"] = df_bvr["budget"].fillna(0)
    df_bvr["ecart"] = df_bvr["budget"] - df_bvr["depenses"]
    df_bvr["ecart_pct"] = df_bvr.apply(
        lambda r: (r["ecart"] / r["budget"] * 100) if r["budget"] != 0 else 0,
        axis=1
    )

    df_bvr_view = df_bvr.copy()
    df_bvr_view["budget"] = df_bvr_view["budget"].apply(euro)
    df_bvr_view["depenses"] = df_bvr_view["depenses"].apply(euro)
    df_bvr_view["ecart"] = df_bvr_view["ecart"].apply(euro)
    df_bvr_view["ecart_pct"] = df_bvr_view["ecart_pct"].map(lambda x: f"{x:.1f} %")

    st.dataframe(
        df_bvr_view[
            ["groupe_charges", "budget", "depenses", "ecart", "ecart_pct"]
        ],
        use_container_width=True
    )

    # ======================================================
    # TABLEAU 2 – DÉTAIL DES DÉPENSES (CRUD)
    # ======================================================
    st.subheader("📋 Détail des dépenses")

    cols_detail = [
        "depense_id",
        "date",
        "compte",
        "poste",
        "montant_ttc",
        "groupe_charges"
    ]

    if "fournisseur" in df_f.columns:
        cols_detail.append("fournisseur")

    df_detail = df_f[cols_detail].copy()

    edited_df = st.data_editor(
        df_detail,
        use_container_width=True,
        num_rows="dynamic",
        key="depenses_editor"
    )

    # ======================================================
    # ENREGISTREMENT
    # ======================================================
    if st.button("💾 Enregistrer les modifications"):
        for _, row in edited_df.iterrows():
            if pd.isna(row["depense_id"]):
                # INSERT
                supabase.table("depenses").insert({
                    "annee": annee,
                    "date": row["date"],
                    "compte": row["compte"],
                    "poste": row["poste"],
                    "montant_ttc": row["montant_ttc"],
                    "fournisseur": row.get("fournisseur")
                }).execute()
            else:
                # UPDATE
                supabase.table("depenses").update({
                    "date": row["date"],
                    "compte": row["compte"],
                    "poste": row["poste"],
                    "montant_ttc": row["montant_ttc"],
                    "fournisseur": row.get("fournisseur")
                }).eq("id", row["depense_id"]).execute()

        st.success("✅ Dépenses enregistrées")
        st.rerun()