from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
)
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import cm

def generate_ag_report(
    filepath,
    annee,
    synthese_poste,
    budget_vs_reel=None,
    pluriannuel=None,
    projection=None,
    economie=None
):
    styles = getSampleStyleSheet()
    story = []

    # --------------------
    # TITRE
    # --------------------
    story.append(Paragraph(
        f"<b>Rapport de gestion – Exercice {annee}</b>",
        styles["Title"]
    ))
    story.append(Spacer(1, 1 * cm))

    story.append(Paragraph(
        "Ce rapport a pour objectif de présenter une analyse factuelle "
        "des charges de l’immeuble, afin d’éclairer les décisions du "
        "conseil syndical et de l’Assemblée Générale.",
        styles["Normal"]
    ))
    story.append(Spacer(1, 1 * cm))

    # --------------------
    # SYNTHÈSE PAR POSTE
    # --------------------
    story.append(Paragraph("<b>1. Synthèse des charges par poste</b>", styles["Heading2"]))
    story.append(Spacer(1, 0.5 * cm))

    table_data = [["Poste", "Montant (€)", "Factures", "Fournisseurs"]]

    for _, r in synthese_poste.iterrows():
        table_data.append([
            r["Poste"],
            f"{r['Montant_Total']:,.0f}",
            r["Nb_Factures"],
            r["Nb_Fournisseurs"]
        ])

    table = Table(table_data, colWidths=[7*cm, 3*cm, 3*cm, 3*cm])
    table.setStyle(TableStyle([
        ("GRID", (0,0), (-1,-1), 0.5, colors.grey),
        ("BACKGROUND", (0,0), (-1,0), colors.lightgrey),
        ("ALIGN", (1,1), (-1,-1), "RIGHT")
    ]))
    story.append(table)
    story.append(Spacer(1, 1 * cm))

    # --------------------
    # BUDGET VS RÉEL
    # --------------------
    if budget_vs_reel is not None:
        story.append(Paragraph("<b>2. Budget voté vs Réel</b>", styles["Heading2"]))
        for _, r in budget_vs_reel.iterrows():
            if r["Statut"].startswith("❌"):
                story.append(Paragraph(
                    f"- Le poste <b>{r['Poste']}</b> dépasse le budget de "
                    f"{r['Écart €']:,.0f} € ({r['Écart %']:.1f} %).",
                    styles["Normal"]
                ))
        story.append(Spacer(1, 1 * cm))

    # --------------------
    # PLURIANNUEL
    # --------------------
    if pluriannuel is not None:
        story.append(Paragraph("<b>3. Tendances pluriannuelles</b>", styles["Heading2"]))
        postes_derives = pluriannuel[
            (pluriannuel["Variation %"] > 10)
            & (~pluriannuel["Variation %"].isna())
        ]
        for _, r in postes_derives.iterrows():
            story.append(Paragraph(
                f"- Le poste <b>{r['Poste']}</b> augmente de "
                f"{r['Variation %']:.1f} % en {int(r['Année'])}.",
                styles["Normal"]
            ))
        story.append(Spacer(1, 1 * cm))

    # --------------------
    # PROJECTION
    # --------------------
    if projection is not None and economie is not None:
        story.append(Paragraph("<b>4. Projection et scénarios</b>", styles["Heading2"]))
        story.append(Paragraph(
            f"Le scénario d’économies simulé permettrait une économie cumulée "
            f"estimée à <b>{economie:,.0f} €</b> sur la période projetée.",
            styles["Normal"]
        ))

    # --------------------
    # GÉNÉRATION
    # --------------------
    doc = SimpleDocTemplate(filepath, pagesize=A4)
    doc.build(story)
