import streamlit as st
import pandas as pd


def etat_depenses_ui(supabase):
    st.header("🧾 État des dépenses")

    tabs = st.tabs(["📊 Consulter", "➕ Ajouter", "✏️ Modifier", "🗑 Supprimer"])

    # ======================================================
    # 📊 CONSULTER
    # ======================================================
    with tabs[0]:
        df = pd.DataFrame(
            supabase.table("depenses").select("*").execute().data
        )

        if df.empty:
            st.info("Aucune dépense enregistrée.")
            return

        # ---------- FILTRES ----------
        f1, f2, f3 = st.columns(3)

        with f1:
            annee = st.selectbox(
                "Année",
                ["Toutes"] + sorted(df["annee"].unique().tolist())
            )

        with f2:
            compte = st.selectbox(
                "Compte",
                ["Tous"] + sorted(df["compte"].dropna().unique().tolist())
            )

        with f3:
            fournisseur = st.selectbox(
                "Fournisseur",
                ["Tous"] + sorted(df["fournisseur"].dropna().unique().tolist())
            )

        if annee != "Toutes":
            df = df[df["annee"] == annee]
        if compte != "Tous":
            df = df[df["compte"] == compte]
        if fournisseur != "Tous":
            df = df[df["fournisseur"] == fournisseur]

        # ---------- KPI ----------
        dep_pos = df[df["montant_ttc"] > 0]["montant_ttc"].sum()
        dep_neg = df[df["montant_ttc"] < 0]["montant_ttc"].sum()

        k1, k2, k3, k4 = st.columns(4)
        k1.metric("Dépenses brutes (€)", f"{dep_pos:,.0f}")
        k2.metric("Avoirs (€)", f"{dep_neg:,.0f}")
        k3.metric("Net (€)", f"{dep_pos + dep_neg:,.0f}")
        k4.metric("Lignes", len(df))

        # ---------- TABLEAU ----------
        if "pdf_url" in df.columns:
            df["Facture"] = df["pdf_url"].apply(
                lambda x: f"[📄 Ouvrir]({x})" if pd.notna(x) else ""
            )

        st.dataframe(
            df.sort_values("date", ascending=False),
            use_container_width=True
        )

    # ======================================================
    # ➕ AJOUTER
    # ======================================================
    with tabs[1]:
        st.subheader("➕ Ajouter une dépense")

        with st.form("add_depense"):
            annee = st.number_input("Année", value=2025)
            compte = st.text_input("Compte")
            poste = st.text_input("Poste")
            fournisseur = st.text_input("Fournisseur")
            date = st.date_input("Date")
            montant = st.number_input("Montant TTC", step=0.01)
            pdf_url = st.text_input("Lien facture (Google Drive / preview)")

            if st.form_submit_button("Enregistrer"):
                supabase.table("depenses").insert({
                    "annee": annee,
                    "compte": compte,
                    "poste": poste,
                    "fournisseur": fournisseur,
                    "date": str(date),
                    "montant_ttc": montant,
                    "pdf_url": pdf_url,
                }).execute()

                st.success("Dépense ajoutée")

    # ======================================================
    # ✏️ MODIFIER
    # ======================================================
    with tabs[2]:
        df = pd.DataFrame(
            supabase.table("depenses").select("*").execute().data
        )

        dep_id = st.selectbox(
            "Dépense",
            df["id"],
            format_func=lambda i: f"{df.loc[df['id']==i, 'poste'].values[0]}"
        )

        dep = df[df["id"] == dep_id].iloc[0]

        new_montant = st.number_input(
            "Montant TTC",
            value=float(dep["montant_ttc"])
        )

        if st.button("Mettre à jour"):
            supabase.table("depenses") \
                .update({"montant_ttc": new_montant}) \
                .eq("id", dep_id) \
                .execute()

            st.success("Dépense mise à jour")

    # ======================================================
    # 🗑 SUPPRIMER
    # ======================================================
    with tabs[3]:
        dep_id = st.selectbox("Dépense à supprimer", df["id"])

        if st.button("Supprimer définitivement"):
            supabase.table("depenses").delete().eq("id", dep_id).execute()
            st.success("Dépense supprimée")