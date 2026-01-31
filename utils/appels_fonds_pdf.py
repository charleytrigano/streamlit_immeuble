
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Table, TableStyle, Spacer
)
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors
from reportlab.lib.units import cm
from io import BytesIO
from datetime import date

from repartition_lots_ui import repartition_lots_ui


def euro(x):
    return f"{x:,.2f} €".replace(",", " ").replace(".", ",")


def generate_pdf_appel_fonds(
    proprietaire,
    annee,
    trimestre,
    lignes_detail,   # list of dicts
    total_trimestre,
    loi_alur
):
    """
    lignes_detail = [
        {"libelle": "...", "montant": 123.45},
        ...
    ]
    """

    buffer = BytesIO()

    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=2 * cm,
        leftMargin=2 * cm,
        topMargin=2 * cm,
        bottomMargin=2 * cm,
    )

    styles = getSampleStyleSheet()
    elements = []

    # ======================================================
    # TITRE
    # ======================================================
    elements.append(Paragraph(
        f"<b>Appel de fonds – Trimestre {trimestre} / {annee}</b>",
        styles["Title"]
    ))
    elements.append(Spacer(1, 12))

    elements.append(Paragraph(
        f"<b>Propriétaire :</b> {proprietaire}",
        styles["Normal"]
    ))
    elements.append(Paragraph(
        f"<b>Date d’édition :</b> {date.today().strftime('%d/%m/%Y')}",
        styles["Normal"]
    ))

    elements.append(Spacer(1, 20))

    # ======================================================
    # TABLEAU DÉTAIL
    # ======================================================
    table_data = [["Nature des charges", "Montant (€)"]]

    for l in lignes_detail:
        table_data.append([
            l["libelle"],
            euro(l["montant"])
        ])

    table_data.append([
        "<b>Loi ALUR (5 %)</b>",
        f"<b>{euro(loi_alur)}</b>"
    ])

    table_data.append([
        "<b>Total appel trimestriel</b>",
        f"<b>{euro(total_trimestre + loi_alur)}</b>"
    ])

    table = Table(table_data, colWidths=[11 * cm, 4 * cm])
    table.setStyle(TableStyle([
        ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
        ("BACKGROUND", (0, 0), (-1, 0), colors.lightgrey),
        ("ALIGN", (1, 1), (-1, -1), "RIGHT"),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("BOTTOMPADDING", (0, 0), (-1, 0), 10),
        ("TOPPADDING", (0, 0), (-1, 0), 10),
    ]))

    elements.append(table)

    # ======================================================
    # FOOTER
    # ======================================================
    elements.append(Spacer(1, 20))
    elements.append(Paragraph(
        "Document généré automatiquement – Ne pas payer sans vérification.",
        styles["Italic"]
    ))

    doc.build(elements)
    buffer.seek(0)

    return buffer
