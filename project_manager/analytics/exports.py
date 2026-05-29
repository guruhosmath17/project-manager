from io import BytesIO

from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas


def build_project_status_pdf(*, project_title: str, lines: list[str]) -> bytes:
    """Create a simple PDF using ReportLab.

    Returns raw PDF bytes.
    """
    buf = BytesIO()
    c = canvas.Canvas(buf, pagesize=A4)
    width, height = A4

    c.setFont("Helvetica-Bold", 16)
    c.drawString(50, height - 50, f"Project Status Report")

    c.setFont("Helvetica", 12)
    c.drawString(50, height - 75, f"Project: {project_title}")

    y = height - 105
    c.setFont("Helvetica", 10)
    for line in lines:
        if y < 60:
            c.showPage()
            y = height - 50
            c.setFont("Helvetica", 10)
        c.drawString(50, y, line[:140])
        y -= 14

    c.showPage()
    c.save()
    return buf.getvalue()

