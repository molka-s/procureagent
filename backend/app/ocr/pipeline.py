"""Pipeline OCR : texte natif PDF d'abord, OCR seulement pour scans/photos.
Sortie : DocumentExtrait (JSON validé Pydantic) avec confiance par champ."""
from pathlib import Path


def texte_natif_pdf(chemin: str) -> str:
    """TODO: PyMuPDF / pdfplumber."""
    return ""


def ocr_image(chemin: str) -> str:
    """TODO: Tesseract (fra+ara) ou PaddleOCR."""
    return ""


def extraire_structure(texte: str) -> dict:
    """TODO: LLM/vision -> JSON validé par DocumentExtrait."""
    raise NotImplementedError


def controles_coherence(doc: dict) -> list[str]:
    """TODO: somme des lignes = total, format de date, TVA plausible."""
    return []


def analyser(chemin: str) -> dict:
    ext = Path(chemin).suffix.lower()
    texte = texte_natif_pdf(chemin) if ext == ".pdf" else ""
    if len(texte.strip()) < 30:
        texte = ocr_image(chemin)
    return extraire_structure(texte)
