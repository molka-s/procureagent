"""Outils de traitement et de vérification des documents déposés."""
import hashlib
from pathlib import Path
from app.ocr.pipeline import analyser
from app.db import get_db_session, text


def calculer_hash_fichier(chemin: str) -> str:
    """Calcule l'empreinte SHA-256 d'un fichier."""
    p = Path(chemin)
    if not p.exists():
        return ""
    hasher = hashlib.sha256()
    with open(p, "rb") as f:
        while chunk := f.read(8192):
            hasher.update(chunk)
    return hasher.hexdigest()


def detecter_doublon(chemin: str) -> bool:
    """Vérifie si le document a déjà été déposé pour une autre demande via son empreinte SHA-256."""
    sha = calculer_hash_fichier(chemin)
    if not sha:
        return False

    requete = text("SELECT id FROM documents WHERE hash_sha256 = :sha LIMIT 1")
    try:
        with get_db_session() as session:
            row = session.execute(requete, {"sha": sha}).fetchone()
            return row is not None
    except Exception:
        return False


def analyser_document(chemin: str) -> dict:
    """Lance le pipeline de numérisation (texte natif ou OCR) sur le document."""
    return analyser(chemin)
