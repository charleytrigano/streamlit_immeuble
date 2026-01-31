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
    # Chargement des dépenses
    # =========================
    resp = (
        supabase
        .table("depenses")
        .select(
            "depense_id, annee, compte, poste, fournisseur, date, montant_ttc"
        )
        .eq("annee", annee)
        .execute()
    )

    if not resp.data:
        st.info("Aucune dépense pour cette année.")
        return

    df = pd.DataFrame(resp.data)

    df["montant_ttc"] = pd.to_numeric(df["montant_ttc"], errors="coerce").fillna(0)
    df["date"] = pd.to_datetime(df["date"], errors="coerce")

    # =========================
    # Filtres
    # =========================
    st.subheader("🔎 Filtres")

    col1, col2 = st.columns(2)

    with col1:
        fournisseurs = ["Tous"] + sorted(df["fournisseur"].dropna().unique().tolist())
        fournisseur_sel = st.selectbox("Fournisseur", fournisseurs)

    with col2:
        comptes = ["Tous"] + sorted(df["compte"].dropna().unique().tolist())
        compte_sel = st.selectbox("Compte", comptes)

    df_f = df.copy()

    if fournisseur_sel != "Tous":
        df_f = df_f[df_f["fournisseur"] == fournisseur_sel]

    if compte_sel != "Tous":
        df_f = df_f[df_f["compte"] == compte_sel]

    if df_f.empty:
        st.warning("Aucune dépense après filtrage.")
        return

    # =========================
    # KPI
    # =========================
    total = df_f["montant_ttc"].sum()
    nb = len(df_f)
    moy = total / nb if nb else 0

    k1, k2, k3 = st.columns(3)
    k1.metric("Total", euro(total))
    k2.metric("Lignes", nb)
    k3.metric("Moyenne", euro(moy))

    # =========================
    # Tableau
    # =========================
    st.subheader("📋 Détail")

    df_f["date"] = df_f["date"].dt.date

    st.dataframe(
        df_f[[
            "date",
            "compte",
            "poste",
            "fournisseur",
            "montant_ttc"
        ]].sort_values("date"),
        use_container_width=True
    )