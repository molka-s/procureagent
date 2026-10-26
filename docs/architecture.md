# Conception et Architecture de ProcureAgent

Ce document formalise les spécifications conceptuelles, logiques et opérationnelles du système ProcureAgent.

---

## 1. Modèle Conceptuel et Relationnel des Données (MLD)

### 1.1 Tables de Référence (Paramétrage Métier)

* **`services`** : Référentiel des départements de l'entreprise.
  * `id` : `SERIAL PRIMARY KEY`
  * `nom` : `TEXT UNIQUE NOT NULL` (ex: 'Design', 'IT', 'RH')

* **`utilisateurs`** : Acteurs humains habilités.
  * `id` : `SERIAL PRIMARY KEY`
  * `email` : `TEXT UNIQUE NOT NULL`
  * `nom_complet` : `TEXT NOT NULL`
  * `role` : `TEXT NOT NULL` (`'demandeur'`, `'acheteur'`, `'validateur'`)
  * `service_id` : `INT REFERENCES services(id)`

* **`budgets`** : Enveloppes budgétaires annuelles.
  * `id` : `SERIAL PRIMARY KEY`
  * `service_id` : `INT REFERENCES services(id)`
  * `annee` : `INT NOT NULL`
  * `montant_total` : `NUMERIC(12,2) NOT NULL`
  * `montant_engage` : `NUMERIC(12,2) NOT NULL DEFAULT 0`
  * *Contrainte* : `UNIQUE (service_id, annee)`

* **`fournisseurs`** : Répertoire des tiers fournisseurs.
  * `id` : `SERIAL PRIMARY KEY`
  * `nom` : `TEXT NOT NULL`
  * `siret` : `TEXT UNIQUE`
  * `autorise` : `BOOLEAN NOT NULL DEFAULT TRUE` (fournisseur homologué)
  * `delai_jours` : `INT DEFAULT 5`

* **`articles`** : Référentiel interne des articles récurrents.
  * `id` : `SERIAL PRIMARY KEY`
  * `reference` : `TEXT UNIQUE NOT NULL`
  * `designation` : `TEXT NOT NULL`
  * `categorie` : `TEXT`

* **`prix_catalogue`** : Grille tarifaire négociée avec les fournisseurs homologués.
  * `fournisseur_id` : `INT REFERENCES fournisseurs(id)`
  * `article_id` : `INT REFERENCES articles(id)`
  * `prix_unitaire_ht` : `NUMERIC(12,2) NOT NULL`
  * *Contrainte* : `PRIMARY KEY (fournisseur_id, article_id)`

* **`regles`** : Paramètres globaux de gestion.
  * `cle` : `TEXT PRIMARY KEY`
  * `valeur` : `NUMERIC NOT NULL` (ex: `seuil_approbation` = 1000, `seuil_confiance_ocr` = 0.85)

---

### 1.2 Tables Opérationnelles (Exécution des Achats)

* **`demandes`** : Trace de chaque intention d'achat.
  * `id` : `UUID PRIMARY KEY`
  * `demandeur_id` : `INT REFERENCES utilisateurs(id)`
  * `service_id` : `INT REFERENCES services(id)`
  * `texte_brut` : `TEXT NOT NULL`
  * `extraction` : `JSONB` (conforme au schéma `DemandeExtraite`)
  * `statut` : `TEXT NOT NULL DEFAULT 'recue'`
  * `cree_le` : `TIMESTAMPTZ DEFAULT now()`

* **`documents`** : Justificatifs déposés (devis, factures proforma).
  * `id` : `SERIAL PRIMARY KEY`
  * `demande_id` : `UUID REFERENCES demandes(id)`
  * `nom_fichier` : `TEXT NOT NULL`
  * `chemin` : `TEXT NOT NULL`
  * `hash_sha256` : `TEXT UNIQUE NOT NULL` (détection anti-doublon)
  * `extraction` : `JSONB` (conforme au schéma `DocumentExtrait`)
  * `confiance_min` : `NUMERIC(4,3)`
  * `verifie_par` : `TEXT`
  * `depose_le` : `TIMESTAMPTZ DEFAULT now()`

* **`commandes`** : Engagements fermes créés après approbation.
  * `id` : `SERIAL PRIMARY KEY`
  * `demande_id` : `UUID UNIQUE REFERENCES demandes(id)`
  * `fournisseur_id` : `INT REFERENCES fournisseurs(id)`
  * `numero_po` : `TEXT UNIQUE NOT NULL` (ex: 'PO-2026-0001')
  * `montant_total_ht` : `NUMERIC(12,2) NOT NULL`
  * `montant_total_ttc` : `NUMERIC(12,2) NOT NULL`
  * `approuve_par_id` : `INT REFERENCES utilisateurs(id) NOT NULL`
  * `approuve_le` : `TIMESTAMPTZ DEFAULT now()`

* **`lignes_commande`** : Détail des postes commandés.
  * `id` : `SERIAL PRIMARY KEY`
  * `commande_id` : `INT REFERENCES commandes(id)`
  * `article_id` : `INT REFERENCES articles(id)`
  * `designation` : `TEXT NOT NULL`
  * `quantite` : `INT NOT NULL`
  * `prix_unitaire_ht` : `NUMERIC(12,2) NOT NULL`

* **`journal_audit`** : Journal immuable de traçabilité.
  * `id` : `BIGSERIAL PRIMARY KEY`
  * `demande_id` : `UUID REFERENCES demandes(id)`
  * `acteur` : `TEXT NOT NULL` ('Agent IA', 'demandeur', 'acheteur', 'validateur')
  * `etape` : `TEXT NOT NULL`
  * `decision` : `TEXT`
  * `raison` : `TEXT`
  * `donnees` : `JSONB`
  * `ts` : `TIMESTAMPTZ DEFAULT now()`

---

## 2. Règles Métier et Gardes-Fous Déterministes

1. **Règle R1 (Complétude)** : Une demande doit obligatoirement résoudre l'article, la quantité (>0) et le service. À défaut, l'agent génère une question précise et s'interrompt en `attente_precisions`.
2. **Règle R2 (Fiabilité Documentaire)** : Tout document dont le score de confiance minimal est inférieur à `seuil_confiance_ocr` (0.85) ou dont la somme des lignes diffère du montant total HT de plus de 0.05 € est orienté vers `attente_correction_ocr`.
3. **Règle R3 (Disponibilité Budgétaire)** : Le montant total engagé ne peut excéder le reliquat du service :
   $$\text{Montant Commande} \le (\text{montant\_total} - \text{montant\_engage})$$
4. **Règle R4 (Fournisseur Agréé)** : Tout achat doit être adossé à un fournisseur dont le fanion `autorise == True`. Tout fournisseur non agréé lève une violation formelle.
5. **Règle R5 (Seuil d'Approbation & Séparation des Tâches)** : Aucun bon de commande ne peut être créé automatiquement par l'IA. Un utilisateur authentifié avec le rôle `validateur` doit expressément signer la commande.
6. **Règle R6 (Anti-doublon)** : Le hash SHA-256 de chaque document déposé est calculé. Tout document déjà présent en base pour une autre commande lève une alerte critique pour tentative de double facturation.

---

## 3. Matrice des Rôles (RBAC)

| Rôle | Périmètre et Autorisations |
|---|---|
| **Demandeur** | Saisir une demande, déposer un devis, répondre aux clarifications (`attente_precisions`), consulter l'avancement de ses propres dossiers. |
| **Acheteur** | Consulter l'ensemble des dossiers, corriger les champs OCR incertains (`attente_correction_ocr`), régulariser les anomalies (`attente_regularisation`), modifier les fournisseurs. |
| **Validateur** | Examiner les dossiers enrichis avec les alertes, valider (`approbation`) pour déclencher la commande, ou rejeter (`refus`) avec saisie obligatoire d'un motif. |
| **Agent IA** | Extraction structurée (LLM), analyse OCR, vérification des règles en lecture seule, préparation du dossier, journalisation de ses étapes. Aucune autorisation d'écriture sur `commandes` ou `budgets`. |

---

## 4. Machine à États (LangGraph) et Points d'Arrêt Humains

```
  START
    │
    ▼
[reception] ──► [comprendre] ──(incomplet)──► [attente_precisions] ──(réponse demandeur)──┐
                      │                                                                   │
                      └─(complet)                                                         │
                            │                                                             │
            ┌───────────────┴───────────────┐                                             │
            ▼                               ▼                                             │
      [Devis joint]                   [Sans devis]                                        │
            │                               │                                             │
            ▼                               │                                             │
   [extraire_document]                      │                                             │
            │                               │                                             │
            ▼                               │                                             │
     [verifier_ocr]                         │                                             │
            │                               │                                             │
      (confiance < 0.85)                    │                                             │
            │                               │                                             │
            ├─► [attente_correction_ocr]    │                                             │
            │          │                    │                                             │
      (confiance OK)   ▼                    │                                             │
            └──────────┴────────────────────┼─────────────────────────────────────────────┘
                                            │
                                            ▼
                                        [enrichir]
                                            │
                                            ▼
                                  [rechercher_fournisseurs]
                                            │
                                            ▼
                                     [verifier_regles]
                                            │
                                            ▼
                                     [preparer_dossier]
                                            │
                       ┌────────────────────┴────────────────────┐
                       ▼                                         ▼
                 (Contrôles OK)                          (Violations/Anomalies)
                       │                                         │
                       ▼                                         ▼
             [presenter_validateur]                      [signaler_probleme]
                       │                                         │
                       ▼                                         ▼
               [attente_decision]                      [attente_regularisation]
                       │                                         │
         ┌─────────────┴─────────────┐                           ├─► (Régularisable) ──► [enrichir]
         ▼                           ▼                           └─► (Non régularisable) ──► [bloquer] ──► END
   (Approbation)                  (Refus)
         │                           │
         ▼                           ▼
  [creer_commande]          [enregistrer_refus]
         │                           │
         ▼                           ▼
    [notifier]                     [END]
         │
         ▼
   [journaliser]
         │
         ▼
       [END]
```
