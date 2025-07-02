from pathlib import Path
from typing import Dict
import markdown
from PyPDF2 import PdfReader, PdfWriter
from pdfminer.high_level import extract_text
# from reportlab.pdfgen import canvas # FIX: Removed unused import
from weasyprint import HTML


def pdf_read(path: str) -> str:
    """Reads text content from a PDF file."""
    try:
        text = extract_text(path)
        return text
    except Exception:
        return ""


def pdf_autofill(path: str, field_dict: Dict) -> str:
    """Autofills specified fields in a PDF form and returns the path to the new PDF."""
    output_path = Path(path).with_name(Path(path).stem + "_filled.pdf")
    try:
        reader = PdfReader(path)
        writer = PdfWriter()
        writer.append_pages_from_reader(reader)
        writer.update_page_form_field_values(writer.pages[0], field_dict)
        with open(output_path, 'wb') as f:
            writer.write(f)
        return str(output_path)
    except Exception:
        return str(output_path)


def pdf_generate(markdown_text: str) -> str:
    """Generates a PDF from Markdown text and returns the path to the new PDF."""
    html = markdown.markdown(markdown_text)
    output = Path("generated.pdf")
    try:
        HTML(string=html).write_pdf(str(output))
        return str(output)
    except Exception:
        return str(output)
