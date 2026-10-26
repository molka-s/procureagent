"""Tests de validation du contrat de données et de l'extraction structurée DemandeExtraite."""
import pytest
from pydantic import ValidationError

from app.schemas.models import DemandeExtraite
from app.agent.nodes.analyse import extraire_demande_llm


def test_schema_demande_extraite_valide():
    """Valide qu'une instance conforme est acceptée par DemandeExtraite."""
    d = DemandeExtraite(
        article="Écran 27 pouces 4K",
        quantite=5,
        service="Design",
        budget=1500.0,
        delai="1 semaine"
    )
    assert d.article == "Écran 27 pouces 4K"
    assert d.quantite == 5
    assert d.service == "Design"
    assert d.budget == 1500.0
    assert d.delai == "1 semaine"


def test_schema_demande_extraite_sans_budget_optionnel():
    """Valide que le champ budget est bien optionnel (None par défaut)."""
    d = DemandeExtraite(
        article="Souris sans fil",
        quantite=2,
        service="IT"
    )
    assert d.budget is None
    assert d.delai is None


def test_schema_demande_extraite_rejet_quantite_invalide():
    """Valide que la quantité doit être strictement positive (> 0)."""
    with pytest.raises(ValidationError):
        DemandeExtraite(article="Clavier", quantite=0, service="IT")

    with pytest.raises(ValidationError):
        DemandeExtraite(article="Clavier", quantite=-3, service="IT")


def test_schema_demande_extraite_rejet_budget_negatif():
    """Valide que le budget ne peut pas être négatif (< 0)."""
    with pytest.raises(ValidationError):
        DemandeExtraite(article="Fauteuil", quantite=1, service="RH", budget=-100.0)


def test_schema_demande_extraite_rejet_champs_vides():
    """Valide que l'article et le service ne peuvent pas être des chaînes vides."""
    with pytest.raises(ValidationError):
        DemandeExtraite(article="", quantite=1, service="RH")

    with pytest.raises(ValidationError):
        DemandeExtraite(article="Écran", quantite=1, service="")


def test_extraction_llm_sortie_structuree_avec_budget():
    """Valide la sortie structurée LLM complète (article, quantité, budget, service)."""
    texte = "Achat de 10 écrans 27 pouces pour le service Design, budget prévisionnel de 3000 euros"
    demande, ok, question, raison = extraire_demande_llm(texte)

    assert ok is True
    assert question is None
    assert isinstance(demande, DemandeExtraite)
    assert "écran" in demande.article.lower()
    assert demande.quantite == 10
    assert demande.service.lower() == "design"
    assert demande.budget == 3000.0


def test_extraction_llm_sortie_structuree_sans_budget():
    """Valide la sortie structurée LLM sans budget explicite."""
    texte = "Besoin urgent de 5 chaises ergonomiques pour le département RH"
    demande, ok, question, raison = extraire_demande_llm(texte)

    assert ok is True
    assert question is None
    assert isinstance(demande, DemandeExtraite)
    assert "chaise" in demande.article.lower()
    assert demande.quantite == 5
    assert demande.service.lower() == "rh"
    assert demande.budget is None


def test_extraction_llm_demande_incomplete_pose_question():
    """Valide qu'une demande incomplète ou vide génère une question précise pour le demandeur."""
    # Demande vide
    demande, ok, question, raison = extraire_demande_llm("")
    assert ok is False
    assert demande is None
    assert question is not None
    assert len(question) > 10

    # Demande sans article ni service
    demande_vague, ok_vague, question_vague, raison_vague = extraire_demande_llm("Bonjour, je souhaite passer une commande")
    assert ok_vague is False
    assert demande_vague is None
    assert question_vague is not None
    assert len(question_vague) > 10

