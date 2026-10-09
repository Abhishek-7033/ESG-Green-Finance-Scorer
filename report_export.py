"""One-page ESG assessment PDF for a company."""
from io import BytesIO
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle

def build_pdf(company, sector, scores, final, rating, penalty, neg,
              flag, flag_msg, drivers, headlines, eligible) -> bytes:
    buf = BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4, leftMargin=40, rightMargin=40, topMargin=40, bottomMargin=40)
    s = getSampleStyleSheet()
    el = [Paragraph(f"ESG Assessment: {company}", s["Title"]),
          Paragraph(f"Sector: {sector}", s["Normal"]), Spacer(1, 12)]

    t = Table([["Final score", "Rating", "Environmental", "Social", "Governance"],
               [f"{final:.0f}/100", rating, f"{scores['E']:.0f}", f"{scores['S']:.0f}", f"{scores['G']:.0f}"]],
              colWidths=[95] * 5)
    t.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#2e7d32")),
                           ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                           ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                           ("GRID", (0, 0), (-1, -1), 0.5, colors.grey)]))
    el += [t, Spacer(1, 14), Paragraph("Key drivers", s["Heading2"])]
    el += [Paragraph(f"• {d}", s["Normal"]) for d in drivers]
    el.append(Paragraph(f"• Controversy penalty: -{penalty:.0f} ({neg} negative news items)", s["Normal"]))
    el += [Spacer(1, 10), Paragraph("Greenwashing check", s["Heading2"]),
           Paragraph(f"<b>{flag}</b>: {flag_msg}", s["Normal"]),
           Spacer(1, 10), Paragraph("Green loan eligibility (indicative)", s["Heading2"]),
           Paragraph("Likely eligible for review" if eligible else "Not yet eligible", s["Normal"]),
           Spacer(1, 10), Paragraph("Recent news signals", s["Heading2"])]
    el += [Paragraph(f"• [{p}/{sn}] {h}", s["Normal"]) for h, p, sn in headlines[:8]] or [Paragraph("None", s["Normal"])]
    el += [Spacer(1, 18), Paragraph("<i>Decision-support output. Verify against primary sources before use.</i>", s["Normal"])]
    doc.build(el)
    return buf.getvalue()
