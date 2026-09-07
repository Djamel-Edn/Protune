"""PDF fixtures, generated at test time rather than committed as binaries."""

import io

import pytest
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas

SAMPLE_CV = [
    "Djamel Dib",
    "Data Engineering apprentice — ESIGELEC, Rouen",
    "djamel@example.com | Chessy, France",
    "",
    "PROFILE",
    "Engineering student specialising in AI and Big Data, looking for a 24-month",
    "apprenticeship starting September 2026.",
    "",
    "PROJECTS",
    "Datathon Alpha AI — first place. Malicious packet detection using KNN and SVM.",
    "MicroHack — first place. Document classification with OCR and deep learning.",
    "Product Sentiment Analyzer — Whisper, Gemini and Streamlit.",
    "",
    "SKILLS",
    "Python, Java, Machine Learning, Oracle SQL, Docker, FastAPI, Next.js",
    "",
    "LANGUAGES",
    "French and Arabic native, English B2 (TOEIC 810)",
]


def build_pdf(lines: list[str], pages: int = 1) -> bytes:
    """A text-based PDF, i.e. one with a real text layer."""
    buffer = io.BytesIO()
    pdf = canvas.Canvas(buffer, pagesize=A4)
    for _ in range(pages):
        y = 800
        for line in lines:
            pdf.drawString(50, y, line)
            y -= 16
        pdf.showPage()
    pdf.save()
    return buffer.getvalue()


def build_imageless_scan() -> bytes:
    """A PDF with no text layer at all — what a scanned CV looks like to pypdf."""
    buffer = io.BytesIO()
    pdf = canvas.Canvas(buffer, pagesize=A4)
    pdf.rect(50, 50, 400, 600, fill=0)
    pdf.showPage()
    pdf.save()
    return buffer.getvalue()


@pytest.fixture
def cv_pdf() -> bytes:
    return build_pdf(SAMPLE_CV)


@pytest.fixture
def scanned_pdf() -> bytes:
    return build_imageless_scan()
