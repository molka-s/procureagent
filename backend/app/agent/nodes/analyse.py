from app.agent.audit import etape
from app.agent import tools
from app.config import settings


@etape("reception")
def reception(s):
    return {"statut": "recue", "_raison": "Demande reçue"}


@etape("comprendre")
def comprendre(s):
    # TODO: LLM -> DemandeExtraite (sortie structurée validée Pydantic)
    texte = s.get("demande_brute", "").strip()
    demande = {"article": texte[:40], "quantite": 1, "service": "Design", "budget": 3000.0} if texte else {}
    return {"demande": demande, "infos_suffisantes": bool(texte), "_raison": "Extraction de la demande"}


@etape("attente_precisions")
def attente_precisions(s):
    return {"statut": "precisions_demandees", "_raison": "Question posée au demandeur"}


@etape("extraire_document")
def extraire_document(s):
    # TODO: tools.analyser_document(...) -> DocumentExtrait + confiance par champ
    return {"document": {"confiance_min": 0.95}, "_raison": "Texte natif ou OCR + extraction structurée"}


@etape("verifier_ocr")
def verifier_ocr(s):
    conf = (s.get("document") or {}).get("confiance_min", 0.0)
    ok = conf >= settings.seuil_confiance_ocr
    return {"ocr_fiable": ok, "_raison": f"confiance min {conf} / seuil {settings.seuil_confiance_ocr}"}


@etape("attente_correction_ocr")
def attente_correction_ocr(s):
    return {"statut": "correction_ocr", "_raison": "Correction humaine des champs extraits"}
