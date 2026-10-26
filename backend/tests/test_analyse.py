"""Tests unitaires de l'extraction LLM et des nœuds d'analyse (backend/app/agent/nodes/analyse.py)."""
import pytest
from app.schemas.models import DemandeExtraite
from app.agent.nodes.analyse import (
    extraire_demande_llm,
    reception,
    comprendre,
    attente_precisions,
    extraire_document,
    verifier_ocr,
    attente_correction_ocr,
)
from app.config import settings


# ============================================================================
# 1. Tests unitaires de la fonction extraire_demande_llm
# ============================================================================

def test_extraire_demande_llm_nominale_complete():
    """Valide l'extraction d'une demande complète avec tous les champs."""
    texte = "Achat de 10 écrans 27 pouces pour le service Design, budget prévisionnel de 3000 euros sous 2 semaines"
    demande, ok, question, raison = extraire_demande_llm(texte)

    assert ok is True
    assert question is None
    assert isinstance(demande, DemandeExtraite)
    assert "écran" in demande.article.lower()
    assert demande.quantite == 10
    assert demande.service.lower() == "design"
    assert demande.budget == 3000.0
    assert demande.delai is not None
    assert len(raison) > 0


def test_extraire_demande_llm_sans_champs_optionnels():
    """Valide l'extraction quand le budget et le délai ne sont pas mentionnés."""
    texte = "Besoin de 5 chaises ergonomiques pour le service RH"
    demande, ok, question, raison = extraire_demande_llm(texte)

    assert ok is True
    assert question is None
    assert isinstance(demande, DemandeExtraite)
    assert "chaise" in demande.article.lower()
    assert demande.quantite == 5
    assert demande.service.lower() == "rh"
    assert demande.budget is None


def test_extraire_demande_llm_quantite_implicite():
    """Valide que l'article mentionné au singulier déduit une quantité égale à 1."""
    texte = "Commande d'un ordinateur portable pour l'équipe IT"
    demande, ok, question, raison = extraire_demande_llm(texte)

    assert ok is True
    assert question is None
    assert isinstance(demande, DemandeExtraite)
    assert "ordinateur" in demande.article.lower()
    assert demande.quantite == 1
    assert demande.service.lower() == "it"


def test_extraire_demande_llm_service_manquant():
    """Valide qu'un service manquant produit infos_suffisantes=False et une question ciblée."""
    texte = "Achat urgent de 3 écrans 27 pouces"
    demande, ok, question, raison = extraire_demande_llm(texte)

    assert ok is False
    assert demande is None
    assert question is not None
    assert len(question) > 10


def test_extraire_demande_llm_quantite_manquante():
    """Valide qu'une quantité indéterminée produit infos_suffisantes=False et une question."""
    texte = "Je voudrais des écrans d'ordinateur pour le service Design"
    demande, ok, question, raison = extraire_demande_llm(texte)

    assert ok is False
    assert demande is None
    assert question is not None
    assert len(question) > 10


def test_extraire_demande_llm_vide():
    """Valide qu'une entrée vide ou blanche est immédiatement rejetée sans crash."""
    for vide in ["", "   ", "\n\t"]:
        demande, ok, question, raison = extraire_demande_llm(vide)
        assert ok is False
        assert demande is None
        assert question is not None
        assert "vide" in raison.lower()


def test_extraire_demande_llm_texte_vague():
    """Valide qu'un texte inintelligible ou trop vague génère une demande de précisions."""
    for vague in ["Bonjour, comment ça va ?", "x", "besoin de trucs"]:
        demande, ok, question, raison = extraire_demande_llm(vague)
        assert ok is False
        assert demande is None
        assert question is not None


# ============================================================================
# 2. Tests unitaires du nœud LangGraph 'comprendre'
# ============================================================================

def test_noeud_comprendre_succes():
    """Valide le format de sortie du nœud comprendre lorsque la demande est complète."""
    etat_initial = {"demande_brute": "10 écrans 27 pouces pour le service Design avec budget de 3000 euros"}
    res = comprendre(etat_initial)

    assert res["infos_suffisantes"] is True
    assert res.get("question_demandeur") is None
    assert isinstance(res["demande"], dict)
    assert res["demande"]["quantite"] == 10
    assert res["demande"]["service"].lower() == "design"
    assert "journal" in res
    assert res["journal"][-1]["etape"] == "comprendre"
    assert len(res["journal"][-1]["raison"]) > 0


def test_noeud_comprendre_incomplet():
    """Valide que le nœud comprendre positionne statut='incomplet' et question_demandeur si info manquante."""
    etat_initial = {"demande_brute": "Besoin urgent d'écrans pour mon équipe"}
    res = comprendre(etat_initial)

    assert res["infos_suffisantes"] is False
    assert res["statut"] == "incomplet"
    assert res["demande"] == {}
    assert res["question_demandeur"] is not None
    assert len(res["question_demandeur"]) > 10
    assert "journal" in res
    assert res["journal"][-1]["etape"] == "comprendre"


def test_noeud_comprendre_demande_vide():
    """Valide le comportement du nœud comprendre face à une demande brute vide."""
    res = comprendre({"demande_brute": ""})

    assert res["infos_suffisantes"] is False
    assert res["statut"] == "incomplet"
    assert res["demande"] == {}
    assert res["question_demandeur"] is not None
    assert "journal" in res


# ============================================================================
# 3. Tests unitaires des autres nœuds d'analyse (reception, attente, OCR)
# ============================================================================

def test_noeud_reception():
    """Valide l'étape de réception initiale."""
    res = reception({})
    assert res["statut"] == "recue"
    assert "journal" in res
    assert res["journal"][-1]["etape"] == "reception"
    assert "Demande reçue" in res["journal"][-1]["raison"]


def test_noeud_attente_precisions():
    """Valide le nœud attente_precisions et la persistance de statut='incomplet'."""
    res = attente_precisions({"question_demandeur": "Quel est votre service ?"})
    assert res["statut"] == "incomplet"
    assert "journal" in res
    assert res["journal"][-1]["etape"] == "attente_precisions"
    assert "Quel est votre service ?" in res["journal"][-1]["raison"]



def test_noeud_extraire_document():
    """Valide le nœud d'extraction documentaire."""
    res = extraire_document({"pieces_jointes": ["devis_1.pdf"]})
    assert "document" in res
    assert res["document"]["confiance_min"] > 0


def test_noeud_verifier_ocr_au_dessus_du_seuil():
    """Valide que la confiance OCR >= 0.85 déclare ocr_fiable=True."""
    res = verifier_ocr({"document": {"confiance_min": 0.95}})
    assert res["ocr_fiable"] is True


def test_noeud_verifier_ocr_en_dessous_du_seuil():
    """Valide qu'une confiance OCR < 0.85 déclare ocr_fiable=False."""
    res = verifier_ocr({"document": {"confiance_min": 0.75}})
    assert res["ocr_fiable"] is False


def test_noeud_attente_correction_ocr():
    """Valide le nœud de mise en pause pour correction OCR humaine."""
    res = attente_correction_ocr({})
    assert res["statut"] == "correction_ocr"
