"""Tests unitaires des outils déterministes de l'agent (Phase 1)."""
import pytest
from app.agent.tools.regles import verifier_budget, verifier_regles, get_budget_info
from app.agent.tools.catalogue import chercher_fournisseurs
from app.agent.tools.commandes import creer_commande, generer_numero_po
from app.agent.tools.documents import calculer_hash_fichier


def test_budget_disponible_design():
    # Design dispose de 38 000 € restants
    info = get_budget_info("Design")
    assert info["trouve"] is True
    assert info["disponible"] >= 3000.0
    assert verifier_budget("Design", 3000.0) is True


def test_budget_insuffisant_rh():
    # RH ne dispose que de 800 € restants
    assert verifier_budget("RH", 1500.0) is False
    assert verifier_budget("RH", 500.0) is True


def test_regles_fournisseur_non_autorise():
    violations = verifier_regles(montant=500.0, fournisseur_autorise=False)
    assert "fournisseur non autorisé" in violations

    violations_ok = verifier_regles(montant=500.0, fournisseur_autorise=True)
    assert len(violations_ok) == 0


def test_catalogue_recherche_ecran():
    fournisseurs = chercher_fournisseurs("écran 27 pouces")
    assert len(fournisseurs) > 0
    # Le premier résultat doit proposer un prix réaliste
    assert fournisseurs[0]["prix_unitaire"] > 0
    assert "nom" in fournisseurs[0]


def test_garde_fou_creation_commande():
    dossier = {"service": "Design", "montant_total": 3000.0}

    # Interdiction stricte sans approbation
    with pytest.raises(PermissionError):
        creer_commande(dossier, approuve_par="")

    # Autorisé avec signature du validateur
    numero = creer_commande(dossier, approuve_par="claire.manager@entreprise.com")
    assert numero.startswith("PO-")


def test_calcul_hash_fichier(tmp_path):
    fichier_test = tmp_path / "devis_test.txt"
    fichier_test.write_text("Devis N°123 - Dell 10 écrans")
    
    sha = calculer_hash_fichier(str(fichier_test))
    assert len(sha) == 64  # Longueur d'un hash SHA-256 en hexadécimal
