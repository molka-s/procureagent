# ProcureAgent

Agent IA de traitement de demandes d'achat : compréhension du texte, lecture OCR des devis, contrôle des règles, **validation humaine avant toute écriture**, création de commande et audit.


## Structure

```
backend/
  app/
    api/routes.py        # endpoints FastAPI
    agent/               # graph.py, state.py, audit.py, nodes/, tools/
    ocr/pipeline.py      # texte natif -> OCR -> extraction JSON
    schemas/models.py    # contrats Pydantic
    config.py main.py
  db/init.sql            # schéma PostgreSQL
  tests/test_graph.py
data/                    # samples/documents, evaluation, uploads
docs/                    # architecture.md, diagramme.png
frontend/                # React + Vite + TypeScript (demande, dossier, validation)
```

## Démarrage

```bash
cp .env.example .env

# Lancer PostgreSQL (Option Docker) :
docker compose up -d

# Backend :
cd backend
pip install -r requirements.txt
python -m pytest
uvicorn app.main:app --reload    # docs API : http://localhost:8000/docs

# Frontend :
cd frontend
npm install
npm run dev                      # interface : http://localhost:5173
```

## API

| Méthode | Route | Rôle |
|---|---|---|
| POST | `/api/documents` | dépose un devis/facture, retourne le chemin |
| POST | `/api/demandes` | `{texte, pieces_jointes}` : lance l'agent jusqu'à la 1re pause |
| GET | `/api/demandes/{id}` | état + noeud en attente |
| POST | `/api/demandes/{id}/reprendre` | `{champs: {decision: "approbation"}}` : reprise humaine |

## Ordre de développement

1. Seed de la base + outils SQL (`agent/tools`)
2. `comprendre` avec le LLM (`DemandeExtraite`)
3. Persistance (PostgresSaver, `journal_audit`)
4. Frontend : écran de vérification OCR avec aperçu du document (les écrans demande, dossier et validation existent déjà)
5. Module OCR
6. Jeu d'évaluation (`data/evaluation`)
