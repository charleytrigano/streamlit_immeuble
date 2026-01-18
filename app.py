# ======================================================
# 📊 ONGLET 3 — BUDGET VS RÉEL (AVEC FILTRES & KPI)
# ======================================================
if page == "📊 Budget vs Réel – Analyse":

    st.subheader("📊 Budget vs Réel – Pilotage")

    # -------- Filtres
    colf1, colf2, colf3 = st.columns(3)

    with colf1:
        annee = st.selectbox(
            "Année",
            sorted(df_dep["annee"].unique())
        )

    with colf2:
        groupes = sorted(df_budget["compte"].str[:2].unique())
        groupe_sel = st.selectbox(
            "Groupe de comptes",
            ["Tous"] + groupes
        )

    with colf3:
        only_over = st.checkbox("Uniquement les dépassements")

    # -------- Données filtrées
    dep = df_dep[df_dep["annee"] == annee].copy()
    bud = df_budget[df_budget["annee"] == annee].copy()

    if groupe_sel != "Tous":
        bud = bud[bud["compte"].str.startswith(groupe_sel)]

    cles_budget = sorted(bud["compte"].unique(), key=len, reverse=True)

    def map_budget(compte):
        for cle in cles_budget:
            if compte.startswith(cle):
                return cle
        return "NON BUDGÉTÉ"

    dep["compte_budget"] = dep["compte"].astype(str).apply(map_budget)

    reel = (
        dep.groupby("compte_budget")["montant_ttc"]
        .sum()
        .reset_index(name="reel")
    )

    comp = bud.merge(
        reel,
        left_on="compte",
        right_on="compte_budget",
        how="left"
    )

    comp["reel"] = comp["reel"].fillna(0)
    comp["ecart_eur"] = comp["reel"] - comp["budget"]
    comp["ecart_pct"] = comp.apply(
        lambda r: (r["ecart_eur"] / r["budget"] * 100)
        if r["budget"] != 0 else 0,
        axis=1
    )

    if only_over:
        comp = comp[comp["ecart_eur"] > 0]

    # -------- KPI
    col1, col2, col3, col4, col5 = st.columns(5)

    total_budget = comp["budget"].sum()
    total_reel = comp["reel"].sum()
    total_ecart = total_reel - total_budget

    col1.metric("Budget (€)", f"{total_budget:,.0f}".replace(",", " "))
    col2.metric("Réel (€)", f"{total_reel:,.0f}".replace(",", " "))
    col3.metric("Écart (€)", f"{total_ecart:,.0f}".replace(",", " "))
    col4.metric(
        "Écart (%)",
        f"{(total_ecart / total_budget * 100):.1f} %" if total_budget != 0 else "-"
    )
    col5.metric(
        "Comptes en dépassement",
        int((comp["ecart_eur"] > 0).sum())
    )

    # -------- Tableau
    st.markdown("### Détail Budget vs Réel")
    st.dataframe(
        comp[["compte", "budget", "reel", "ecart_eur", "ecart_pct"]],
        use_container_width=True
    )
