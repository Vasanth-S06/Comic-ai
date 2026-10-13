import base64
from io import BytesIO

from fpdf import FPDF


class ComicPDF(FPDF):
    def footer(self):
        self.set_y(-15)
        self.set_font("Helvetica", size=8)
        self.cell(0, 10, f"ComicCraft - Page {self.page_no()}", align="C")


def safe_text(value):
    value = str(value or "")
    return value.encode("latin-1", "replace").decode("latin-1")


def _decode_data_url(data_url):
    if not isinstance(data_url, str) or not data_url.startswith("data:image/"):
        return None
    try:
        return base64.b64decode(data_url.split(",", 1)[1])
    except Exception:
        return None


def build_comic_pdf(title, panels):
    pdf = ComicPDF()
    pdf.set_auto_page_break(auto=True, margin=15)

    for index, panel in enumerate(panels, start=1):
        pdf.add_page()
        pdf.set_font("Helvetica", "B", 18)
        pdf.multi_cell(0, 10, safe_text(title), new_x="LMARGIN", new_y="NEXT")
        pdf.ln(2)

        pdf.set_font("Helvetica", "B", 13)
        pdf.multi_cell(0, 8, safe_text(f"Panel {index}: {panel.get('title', '')}"),
                       new_x="LMARGIN", new_y="NEXT")
        pdf.ln(3)

        raw = _decode_data_url(panel.get("image_url", ""))
        if raw:
            pdf.image(BytesIO(raw), x=15, w=180)  # 4:3 image -> 135 mm tall
            pdf.ln(4)

        pdf.set_font("Helvetica", size=11)
        pdf.multi_cell(0, 7, safe_text(panel.get("narration", "")), new_x="LMARGIN", new_y="NEXT")
        pdf.ln(3)

        pdf.set_font("Helvetica", "I", size=11)
        pdf.multi_cell(0, 7, safe_text(panel.get("dialogue", "")), new_x="LMARGIN", new_y="NEXT")

    return bytes(pdf.output())
